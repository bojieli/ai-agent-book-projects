## Android Environment Setup Guide

This guide will help you set up a local Android environment for AgentWorld.

### Installation Steps

1. **Download and Install Android Studio**
   - Visit [https://developer.android.com/studio](https://developer.android.com/studio)
   - Download and install the latest version for your operating system

2. **Install ADB and Android Emulator**
   - Open Android Studio
   - Click on the top menu: Tools → SDK Manager
        <img src="../../../readme_assets/android_step1.png" width="70%" alt="SDK Manager">
       <!-- ![Agent World Framework](../../readme_assets/android_step1.png){:style="width:200px; height:auto;"} -->
   - Check the following components:
     - Android SDK Build-Tools
     - Android SDK Command-line Tools
     - Android Emulator
     - Android SDK Platform-Tools
   - Click "Apply" to install these components
      <img src="../../../readme_assets/android_step2.png" width="70%" alt="Check components">
   - **Important**: Copy the installation directory path (you'll need it later for configuration)

3. **Create a Virtual Device**
   - From the main menu, select: View → Tool Windows → Device Manager
    <img src="../../../readme_assets/android_step3.png" width="70%" alt="Device Manager">
   - Click the "+" button, then "Create Virtual Device"
   <img src="../../../readme_assets/android_step4.png" width="70%" alt="button">
   - Select a device (e.g., Medium Phone), then click "Next"
   <img src="../../../readme_assets/android_step5.png" width="70%" alt="next">
   - Select a image (e.g., VanillalceCream), then click "Next"
   <img src="../../../readme_assets/android_step6.png" width="70%" alt="next">
   - Configure device settings as needed, then click "Finish"
   - **Important**: Note down the AVD ID (device name) for later use
   <img src="../../../readme_assets/android_step7.png" width="70%" alt="avd id">

4. **Configure in Your Code**
   - Method 1: Default Acquisition of Emulator and ADB Installation Paths
     - Only set the AVD_ID copied during the earlier installation process.
   - Method 2: Manually Specify Emulator and ADB Installation Paths.Provide the following:
     - AVD_ID: The name of the virtual device you created
     - ADB path: Your SDK directory + "/platform-tools/adb"
     - Emulator path: Your SDK directory + "/emulator/emulator"
### Example Code
#### Method 1

```python
from examples.common.tools.android.action.adb_controller import ADBController

# Initialize the Android controller
android_controller = ADBController(avd_name="Medium_Phone_API_35")
```
#### Method 2

```python
from examples.common.tools.android.action.adb_controller import ADBController

# Initialize the Android controller
android_controller = ADBController(
    avd_name="Medium_Phone_API_35",
    adb_path="/Users/username/Library/Android/sdk/platform-tools/adb",
    emulator_path="/Users/username/Library/Android/sdk/emulator/emulator"
)

# Now you can use this controller with your agent
```

### Troubleshooting

- If the emulator fails to start, try increasing the memory allocation in the AVD settings
- Make sure your paths are correct for your operating system:
  - Windows: Use backslashes or raw strings (r"C:\path\to\sdk")
  - macOS/Linux: Use forward slashes as shown in the example

### Additional Resources

- [Android SDK Official Documentation](https://developer.android.com/studio/intro)
- [Android Emulator Documentation](https://developer.android.com/studio/run/emulator)