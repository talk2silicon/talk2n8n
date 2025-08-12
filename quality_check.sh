#!/bin/bash
# Quality check script following talk2browser pattern
# Run all quality checks locally before committing

echo "🔍 Running quality checks for talk2n8n..."
echo ""

echo "🧹 Running flake8..."
flake8 src/ tests/
if [ $? -ne 0 ]; then
    echo "❌ flake8 failed"
    exit 1
fi
echo "✅ flake8 passed"
echo ""

echo "🎨 Checking black formatting..."
black --check src/ tests/
if [ $? -ne 0 ]; then
    echo "❌ black formatting failed"
    echo "💡 Run 'black src/ tests/' to fix formatting"
    exit 1
fi
echo "✅ black formatting passed"
echo ""

echo "🔍 Running mypy..."
mypy src/talk2n8n
if [ $? -ne 0 ]; then
    echo "❌ mypy failed"
    exit 1
fi
echo "✅ mypy passed"
echo ""

# Check if we should skip tests
if [ "$SKIP_TESTS" = "true" ]; then
    echo "⏭️  Skipping tests (SKIP_TESTS=true)"
else
    echo "🧪 Running tests..."
    # Check if there are any test files
    if find tests/ -name "test_*.py" -o -name "*_test.py" | grep -q .; then
        pytest
        if [ $? -ne 0 ]; then
            echo "❌ tests failed"
            exit 1
        fi
        echo "✅ tests passed"
    else
        echo "⚠️  No test files found - skipping tests"
        echo "💡 Consider adding tests in the tests/ directory"
    fi
fi
echo ""

echo "🎉 All quality checks passed!"
echo "Your code is ready for commit."
