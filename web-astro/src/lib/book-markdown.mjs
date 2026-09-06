const originalSite = 'https://bojieli.github.io/ai-agent-book';

// Adapt the web view only. The tracked book remains the shared PDF/website source.
export function bookMarkdown() {
  return (tree) => {
    if (tree.children[0]?.type === 'heading' && tree.children[0].depth === 1) {
      tree.children.shift();
    }
    const walk = (node) => {
      if (
        node.type === 'paragraph' &&
        node.children?.length === 1 &&
        node.children[0].type === 'image'
      ) {
        node.data = { ...node.data, hName: 'figure' };
        node.children.push({
          type: 'paragraph',
          data: { hName: 'figcaption' },
          children: [{ type: 'text', value: node.children[0].alt ?? '' }],
        });
      }
      if (node.type === 'image' && node.url.startsWith('images/')) {
        node.url = `/book-en/${node.url}`;
      }
      if (
        node.type === 'link' &&
        !/^(?:[a-z][a-z\d+.-]*:|#|\/)/i.test(node.url)
      ) {
        if (/^chapter1\.md(?:#|$)/.test(node.url)) {
          node.url = node.url.replace('chapter1.md', '/book-en/chapter1/');
        } else {
          const resolved = new URL(node.url, `${originalSite}/book-en/`);
          resolved.pathname = resolved.pathname.replace(/\.md$/, '/');
          node.url = resolved.href;
        }
      }
      node.children?.forEach(walk);
    };
    walk(tree);
  };
}
