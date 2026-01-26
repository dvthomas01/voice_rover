# ESP32 Tests

ESP32 unit tests can be implemented using PlatformIO's testing framework.

## Running Tests

```bash
cd esp32
pio test
```

## Test Structure

Tests should be placed in `esp32/test/` directory and follow PlatformIO test conventions.

Example test file: `test_balance_controller.cpp`

```cpp
#include <unity.h>
#include "balance/balance_controller.h"

void test_balance_controller_initialization() {
    BalanceController controller(1.0, 0.1, 0.05);
    TEST_ASSERT_TRUE(true);  // Placeholder
}

void setup() {
    UNITY_BEGIN();
    RUN_TEST(test_balance_controller_initialization);
    UNITY_END();
}

void loop() {
    // Tests run once in setup()
}
```

## Test Coverage

Priority test areas:
- Balance controller PID calculations
- Motor driver direction and speed control
- Command handler JSON parsing and validation
- Serial communication error handling
