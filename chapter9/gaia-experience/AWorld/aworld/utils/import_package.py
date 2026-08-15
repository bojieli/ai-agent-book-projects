# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import os.path
import time
import sys
import importlib
import subprocess
from importlib import metadata
from aworld.logs.util import logger


class ModuleAlias:
    def __init__(self, module):
        self.module = module

    def __getattr__(self, name):
        return getattr(self.module, name)


def is_package_installed(package_name: str, version: str = "") -> bool:
    """
    Check if package is already installed and matches version if specified.

    Args:
        package_name: Name of the package to check
        version: Required version of the package

    Returns:
        bool: True if package is installed (and version matches if specified), False otherwise
    """
    try:
        dist = metadata.distribution(package_name)

        if version and dist.version != version:
            logger.info(f"Package {package_name} is installed but version {dist.version} "
                        f"does not match required version {version}")
            return False

        logger.info(f"Package {package_name} is already installed (version: {dist.version})")
        return True

    except metadata.PackageNotFoundError:
        logger.info(f"Package {package_name} is not installed")
        return False
    except Exception as e:
        logger.warning(f"Error checking if {package_name} is installed: {str(e)}")
        return False


def import_packages(packages: list[str]) -> dict:
    """
    Import and install multiple packages

    Args:
        packages: List of packages to import

    Returns:
        dict: Dictionary mapping package names to imported modules
    """
    modules = {}
    for package in packages:
        package_ = import_package(package)
        if package_:
            modules[package] = package_
    return modules


def import_package(
        package_name: str,
        alias: str = '',
        install_name: str = '',
        version: str = '',
        installer: str = 'pip',
        timeout: int = 300,
        retry_count: int = 3,
        retry_delay: int = 5
) -> object:
    """
    Import and install package if not available.

    Args:
        package_name: Name of the package to import
        alias: Alias to use for the imported module
        install_name: Name of the package to install (if different from import name)
        version: Required version of the package
        installer: Package installer to use ('pip' or 'conda')
        timeout: Installation timeout in seconds
        retry_count: Number of installation retries if install fails
        retry_delay: Delay between retries in seconds

    Returns:
        Imported module

    Raises:
        ValueError: If input parameters are invalid
        ImportError: If package cannot be imported or installed
        TimeoutError: If installation exceeds timeout
    """
    # Validate input parameters
    if not package_name:
        raise ValueError("Package name cannot be empty")

    if installer not in ['pip', 'conda']:
        raise ValueError(f"Unsupported installer: {installer}")

    # Use package_name as install_name if not provided
    real_install_name = install_name if install_name else package_name

    # First, check if we need to install the package
    need_install = False

    # Try to import the module first
    try:
        logger.debug(f"Attempting to import {package_name}")
        module = importlib.import_module(package_name)
        logger.debug(f"Successfully imported {package_name}")

        # If we successfully imported the module, check version if specified
        if version:
            try:
                # For packages with different import and install names,
                # we need to check the install name for version info
                installed_version = metadata.version(real_install_name)
                if installed_version != version:
                    logger.warning(
                        f"Package {real_install_name} version mismatch. "
                        f"Required: {version}, Installed: {installed_version}"
                    )
                    need_install = True
            except metadata.PackageNotFoundError:
                logger.warning(f"Could not determine version for {real_install_name}")

        # If no need to reinstall for version mismatch, return the module
        if not need_install:
            return ModuleAlias(module) if alias else module

    except ImportError as import_err:
        logger.info(f"Could not import {package_name}: {str(import_err)}")
        # Check if the package is installed
        if not is_package_installed(real_install_name, version):
            need_install = True
        else:
            # If package is installed but import failed, there might be an issue with dependencies
            # or the package itself. Still, let's try to reinstall it.
            logger.warning(f"Package {real_install_name} is installed but import of {package_name} failed. "
                           f"Will attempt reinstallation.")
            need_install = True

    # Install the package if needed
    if need_install:
        logger.info(f"Installation needed for {real_install_name}")

        # Attempt installation with retries
        for attempt in range(retry_count):
            try:
                cmd = _get_install_command(installer, real_install_name, version)
                logger.info(f"Installing {real_install_name} with command: {' '.join(cmd)}")
                _execute_install_command(cmd, timeout)

                # Break out of retry loop if installation succeeds
                break

            except (ImportError, TimeoutError, subprocess.SubprocessError) as e:
                if attempt < retry_count - 1:
                    logger.warning(
                        f"Installation attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"All installation attempts failed for {real_install_name}")
                    raise ImportError(f"Failed to install {real_install_name} after {retry_count} attempts: {str(e)}")

    # Try importing after installation
    try:
        logger.debug(f"Attempting to import {package_name} after installation")
        module = importlib.import_module(package_name)
        logger.debug(f"Successfully imported {package_name}")
        return ModuleAlias(module) if alias else module
    except ImportError as e:
        error_msg = f"Failed to import {package_name} even after installation of {real_install_name}: {str(e)}"
        logger.error(error_msg)


def _get_install_command(installer: str, package_name: str, version: str = "") -> list:
    """
    Generate installation command based on specified installer.

    Args:
        installer: Package installer to use ('pip' or 'conda')
        package_name: Name of the package to install
        version: Required version of the package

    Returns:
        list: Command as a list of strings

    Raises:
        ValueError: If unsupported installer is specified
    """
    if installer == 'pip':
        # Use sys.executable to ensure the right Python interpreter is used
        pytho3 = os.path.basename(sys.executable)
        cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade']
        if version:
            cmd.append(f'{package_name}=={version}')
        else:
            cmd.append(package_name)
    elif installer == 'conda':
        cmd = ['conda', 'install', '-y', package_name]
        if version:
            cmd.extend([f'={version}'])
    else:
        raise ValueError(f"Unsupported installer: {installer}")

    return cmd


def _execute_install_command(cmd: list, timeout: int) -> None:
    """
    Execute package installation command.

    Args:
        cmd: Installation command as list of strings
        timeout: Installation timeout in seconds

    Raises:
        TimeoutError: If installation exceeds timeout
        ImportError: If installation fails
    """
    logger.info(f"Executing: {' '.join(cmd)}")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        stdout, stderr = process.communicate(timeout=timeout)

        # Log installation output for debugging
        if stdout:
            logger.debug(f"Installation stdout: {stdout.decode()}")
        if stderr:
            logger.debug(f"Installation stderr: {stderr.decode()}")

    except subprocess.TimeoutExpired:
        process.kill()
        error_msg = f"Package installation timed out after {timeout} seconds"
        logger.error(error_msg)
        raise TimeoutError(error_msg)

    if process.returncode != 0:
        error_msg = f"Installation failed with code {process.returncode}: {stderr.decode()}"
        logger.error(error_msg)
        raise ImportError(error_msg)

    logger.info("Installation completed successfully")