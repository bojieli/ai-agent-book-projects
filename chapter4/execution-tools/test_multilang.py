"""Test multi-language code execution."""

import asyncio
import sys
from multilang_executor import LanguageExecutor, ExecutionStatus


async def run_language_case(executor: LanguageExecutor, language: str, code: str, description: str):
    """Test a specific language."""
    print(f"\n{'='*60}")
    print(f"Testing {language}: {description}")
    print(f"{'='*60}")
    
    result = await executor.execute_code(code, language, timeout=10.0)
    
    print(f"Status: {result.get('status')}")
    if result.get('stdout'):
        print(f"Output:\n{result['stdout']}")
    if result.get('stderr'):
        print(f"Errors:\n{result['stderr']}")
    if result.get('compile_output'):
        print(f"Compile output:\n{result['compile_output']}")
    
    success = result.get('status') == ExecutionStatus.SUCCESS
    print(f"✅ PASSED" if success else f"❌ FAILED")
    return success


async def main():
    """Run all language tests."""
    executor = LanguageExecutor()
    
    tests = [
        # Python
        ("python", """
import numpy as np
import pandas as pd

data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print("Data shape:", data.shape)
print("Mean of A:", data['A'].mean())
""", "NumPy and Pandas"),
        
        # JavaScript
        ("javascript", """
console.log('Hello from Node.js!');
const numbers = [1, 2, 3, 4, 5];
const sum = numbers.reduce((a, b) => a + b, 0);
console.log('Sum:', sum);
""", "Array operations"),
        
        # TypeScript
        ("typescript", """
interface Point {
    x: number;
    y: number;
}

const point: Point = { x: 10, y: 20 };
console.log(`Point: (${point.x}, ${point.y})`);
""", "Type-safe interfaces"),
        
        # Go
        ("go", """
package main

import "fmt"

func main() {
    fmt.Println("Hello from Go!")
    sum := 0
    for i := 1; i <= 10; i++ {
        sum += i
    }
    fmt.Printf("Sum of 1-10: %d\\n", sum)
}
""", "Loops and formatting"),
        
        # Java
        ("java", """
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
        int sum = 0;
        for (int i = 1; i <= 10; i++) {
            sum += i;
        }
        System.out.println("Sum of 1-10: " + sum);
    }
}
""", "Basic class and loops"),
        
        # C++
        ("cpp", """
#include <iostream>
#include <vector>
#include <numeric>

int main() {
    std::cout << "Hello from C++!" << std::endl;
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    int sum = std::accumulate(numbers.begin(), numbers.end(), 0);
    std::cout << "Sum: " << sum << std::endl;
    return 0;
}
""", "STL vector and accumulate"),
        
        # Rust
        ("rust", """
fn main() {
    println!("Hello from Rust!");
    let numbers = vec![1, 2, 3, 4, 5];
    let sum: i32 = numbers.iter().sum();
    println!("Sum: {}", sum);
}
""", "Vector and iterators"),
        
        # PHP
        ("php", """
<?php
echo "Hello from PHP!\\n";
$numbers = [1, 2, 3, 4, 5];
$sum = array_sum($numbers);
echo "Sum: $sum\\n";
?>
""", "Array operations"),
        
        # Bash
        ("bash", """
echo "Hello from Bash!"
sum=0
for i in {1..10}; do
    sum=$((sum + i))
done
echo "Sum of 1-10: $sum"
""", "Shell loops"),
    ]
    
    print(f"\n{'#'*60}")
    print(f"# Multi-Language Code Execution Test Suite")
    print(f"{'#'*60}")
    
    results = []
    for language, code, description in tests:
        try:
            success = await run_language_case(executor, language, code, description)
            results.append((language, success))
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            results.append((language, False))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for language, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {language}")
    
    print(f"\nTotal: {passed}/{total} passed ({100*passed//total}%)")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
