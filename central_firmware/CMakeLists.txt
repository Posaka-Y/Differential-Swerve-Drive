cmake_minimum_required(VERSION 3.16)
project(differential_swerve_central_core LANGUAGES CXX)

add_library(differential_swerve_central_core
    src/control/swerve_coordinator.cpp
    src/control/steer_trajectory.cpp
    src/control/arm_controller.cpp
)
target_include_directories(differential_swerve_central_core PUBLIC include)
target_compile_features(differential_swerve_central_core PUBLIC cxx_std_11)
target_compile_options(differential_swerve_central_core PRIVATE
    -Wall -Wextra -Wpedantic -Werror
)

add_executable(swerve_coordinator_test
    tests/swerve_coordinator_test.cpp
)
target_link_libraries(swerve_coordinator_test PRIVATE
    differential_swerve_central_core
)
target_compile_options(swerve_coordinator_test PRIVATE
    -Wall -Wextra -Wpedantic -Werror
)

enable_testing()
add_test(NAME swerve_coordinator_test COMMAND swerve_coordinator_test)
