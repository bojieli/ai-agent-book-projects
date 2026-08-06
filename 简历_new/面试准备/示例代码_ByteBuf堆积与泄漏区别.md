# ByteBuf 堆积 vs 泄漏：代码示例

> 对应项目一 OOM 场景：ES 写慢 → 队列积压 → ByteBuf 引用未释放 → 堆外占用上升

---

## 1. 问题链路示意

```
Netty 接收 → ByteBuf 入队 → 异步线程消费写 ES
                ↑                    ↓
            队列积压时              ES 写慢
            ByteBuf 一直被引用      消费变慢
            → release() 调不到      → 队列越来越长
            → 堆外内存持续涨
```

---

## 2. 简化代码：有问题的写法（会堆积）

```java
// 伪代码：问题链路
public class AuditChannelHandler extends ChannelInboundHandlerAdapter {

    // 无界队列：ES 写慢时，这里会无限堆积
    private final BlockingQueue<ByteBuf> writeQueue = new LinkedBlockingQueue<>();

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        ByteBuf buf = (ByteBuf) msg;
        buf.retain();  // 引用 +1，因为要交给异步线程
        writeQueue.offer(buf);  // 入队，buf 被队列持有
        // 此时 buf 的 refCnt > 0，堆外内存不会释放
    }

    // 异步消费线程
    void consumeAndWriteToES() {
        while (true) {
            ByteBuf buf = writeQueue.take();  // 阻塞取
            try {
                // 模拟：ES 写慢时，这里会卡很久
                esClient.index(buf);
            } finally {
                buf.release();  // 只有写完了才 release
            }
        }
    }
}
```

**关键点**：
- `buf.retain()` 后，引用计数 > 0
- 只要 `buf` 还在 `writeQueue` 里，`release()` 就不会被调用
- ES 写慢 → 消费慢 → 队列堆积 → 大量 ByteBuf 被队列引用 → 堆外内存涨

---

## 3. 堆积 vs 泄漏 的判断依据

```java
// 堆积：压力下来后，队列会慢慢消费完，内存回落
// 泄漏：压力下来后，内存不回落（对象永远不被 GC）

// 判断方式：压测前后对比
// 1. 压测 2 万 QPS 长稳 1 小时 → direct memory 涨到 1.2G 触发 OOM
// 2. 停止压测，等待 10 分钟
// 3. 堆积：内存会慢慢回落（队列消费完，ByteBuf 逐个 release）
// 4. 泄漏：内存不回落（有对象永远没 release）
```

---

## 4. 修复思路：有界队列 + 降级

```java
public class AuditChannelHandler extends ChannelInboundHandlerAdapter {

    // 有界队列：满了就降级，不无限堆积
    private static final int QUEUE_CAPACITY = 5000;
    private final BlockingQueue<ByteBuf> writeQueue = new LinkedBlockingQueue<>(QUEUE_CAPACITY);

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        ByteBuf buf = (ByteBuf) msg;
        buf.retain();

        if (!writeQueue.offer(buf)) {
            // 队列满了，降级：丢弃 + 告警，立即 release
            buf.release();
            dropCounter.increment();
            alertIfNeeded();
            return;
        }
    }

    void consumeAndWriteToES() {
        while (true) {
            ByteBuf buf = writeQueue.poll(100, TimeUnit.MILLISECONDS);
            if (buf == null) continue;
            try {
                esClient.index(buf);
            } finally {
                buf.release();  // 无论成功失败都要 release
            }
        }
    }
}
```

---

## 5. 引用计数要点（面试可背）

| 操作 | 时机 | 说明 |
|------|------|------|
| `retain()` | 交给异步线程前 | 防止当前线程 release 后，异步线程还在用 |
| `release()` | 用完后 | 必须调用，否则堆外不释放 |
| 队列持有 | 持有期间 refCnt > 0 | 队列积压 = 大量 ByteBuf 同时 refCnt > 0 |

**结论**：堆外 OOM 不是「泄漏」，而是「高峰堆积」——队列有界 + 超限降级后，内存可控。

---

## 6. Netty 内存池参数优化（PooledByteBufAllocator）

> 对应面试答案：arena 数量从默认 CPU×2 调到与 worker 线程数对齐，tiny/small cache 按实际分配尺寸分布做了放大

### 6.1 默认行为 vs 优化后

```java
// Netty PooledByteBufAllocator 默认构造
// - nHeapArena / nDirectArena = Runtime.getRuntime().availableProcessors() * 2
// - 多个 worker 线程可能争同一个 arena，高并发下竞争明显

// 优化思路：arena 数 ≈ worker 线程数，减少争用
```

### 6.2 自定义 Allocator 配置

```java
import io.netty.buffer.PooledByteBufAllocator;
import io.netty.channel.ChannelOption;

// Worker 线程数（与 NioEventLoopGroup 的线程数一致）
int workerThreads = 16;

// 默认：nHeapArena = nDirectArena = CPU * 2
// 问题：多个 worker 争同一 arena，高并发下竞争明显
// 优化：arena 数 = worker 数，减少争用
PooledByteBufAllocator allocator = new PooledByteBufAllocator(
        true,           // preferDirect
        workerThreads,   // nHeapArena
        workerThreads,   // nDirectArena
        8192,           // pageSize
        11,             // maxOrder
        512,             // tinyCacheSize，小包多可调大
        256,             // smallCacheSize，按分配尺寸分布调大
        64,              // normalCacheSize
        true             // useCacheForAllThreads
);

bootstrap.option(ChannelOption.ALLOCATOR, allocator);
bootstrap.childOption(ChannelOption.ALLOCATOR, allocator);
```

### 6.3 通过系统属性配置（更常用）

```java
// Netty 支持通过系统属性配置，启动时加 JVM 参数：

// arena 数量（direct 和 heap 分别配置）
// -Dio.netty.allocator.numDirectArenas=16
// -Dio.netty.allocator.numHeapArenas=16

// tiny/small cache 大小（每个线程的本地缓存条数）
// -Dio.netty.allocator.tinyCacheSize=512
// -Dio.netty.allocator.smallCacheSize=256
// 若实际分配以 256~512 字节为主，可把 smallCacheSize 调到 512

// 启动时
java -Dio.netty.allocator.numDirectArenas=16 \
     -Dio.netty.allocator.numHeapArenas=16 \
     -Dio.netty.allocator.smallCacheSize=512 \
     -jar your-app.jar
```

### 6.4 参数含义速查

| 参数 | 默认 | 优化思路 |
|------|------|----------|
| `numDirectArenas` | CPU×2 | 调到与 worker 线程数一致，减少 arena 争用 |
| `numHeapArenas` | CPU×2 | 同上 |
| `tinyCacheSize` | 512 | 小包多时适当放大，减少向 arena 申请 |
| `smallCacheSize` | 256 | 同上，按 256~512 字节区间分配量调整 |

### 6.5 验证方式

```java
// 压测前后对比
// 1. direct.memory 曲线：改前缓慢上涨到 1.2G OOM，改后稳定在 400M 以内
// 2. GC 停顿：arena 争用减少，停顿更平滑
// 3. 队列积压：配合有界队列，不再无限堆积
```
