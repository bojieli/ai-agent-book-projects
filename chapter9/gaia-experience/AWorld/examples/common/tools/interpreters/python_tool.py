import sys
import ast
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Tuple, List
from io import StringIO

from aworld.logs.util import logger
from aworld.config.conf import ToolConfig
from examples.common.tools.tool_action import PythonToolAction
from aworld.core.common import ActionModel, Observation, ActionResult
from aworld.core.tool.base import Tool, AgentInput, ToolFactory
from aworld.utils import import_package
from aworld.tools.utils import build_observation


@ToolFactory.register(name="python_execute",
                      desc="python interpreter tool",
                      supported_action=PythonToolAction,
                      conf_file_name=f'python_execute_tool.yaml',
                      dir=f"{Path(__file__).parent.absolute()}")
class PythonTool(Tool):

    def __init__(self,
                 conf: ToolConfig,
                 **kwargs) -> None:
        """
        Initialize the PythonExecutor
        Args:
            conf: tool config
            **kwargs: -
        Return:
            None
        """
        super(PythonTool, self).__init__(conf, **kwargs)
        self.type = "function"
        self.local_namespace = {}
        self.global_namespace = {}
        self.original_stdout = sys.stdout
        self.output_buffer = StringIO()
        self.installed_packages = set()
        import_package('langchain_experimental')
        from langchain_experimental.utilities.python import PythonREPL
        self.python_repl = PythonREPL()

    def extract_imports(self, code: str) -> set:
        """
        Extract import statements
        Args:
            code: python code
        Returns:
            set: import statements
        """
        imports = set()

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # deal import xxx or import xxx as yyy
                    for name in node.names:
                        package_name = name.name.split('.')[0]
                        imports.add(package_name)

                elif isinstance(node, ast.ImportFrom):
                    # deal from xxx import yyy or from xxx.yyy import zzz
                    if node.module:
                        package_name = node.module.split('.')[0]
                        imports.add(package_name)

        except SyntaxError:
            import_pattern = r'^import\s+([\w\s,]+)|from\s+(\w+)'
            for line in code.split('\n'):
                line = line.strip()
                match = re.match(import_pattern, line)
                if match:
                    if match.group(1):

                        packages = [p.strip() for p in match.group(1).split(',')]
                        for package in packages:
                            if package:
                                package_name = package.split()[0]
                                imports.add(package_name)
                    elif match.group(2):
                        imports.add(match.group(2))

        return imports

    def install_dependencies(self,
                             packages: set) -> None:
        """
        Install dependency packages
        Args:
            packages: python third packages
        Returns:
            None
        """
        for package in packages:
            try:
                __import__(package)
            except ImportError:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    self.installed_packages.add(package)
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to install {package}: {str(e)}")

    def uninstall_dependencies(self) -> None:
        """
        Uninstall dependency packages
        Args:
            -
        Returns:
            None
        """
        try:
            for package in self.installed_packages:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", package])
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to uninstall {package}: {str(e)}")
            self.installed_packages.clear()
        except Exception as e:
            logger.warning(f"Failed to uninstall dependencies: {repr(e)}")

    def reset(self,
              *,
              seed: int | None = None,
              options: Dict[str, str] | None = None) -> Tuple[AgentInput, dict[str, Any]]:
        """
        Reset the executor
        Args:
            seed: -
            options: -
        Returns:
            AgentInput, dict[str, Any]: -
        """
        self.close()
        self.local_namespace = {}
        self.global_namespace = {}
        self._finished = False
        self.installed_packages.clear()

        return build_observation(observer=self.name(),
                                 ability=PythonToolAction.EXECUTE.value.name), {}

    def close(self) -> None:
        """
        Close the executor
        Returns:
            None
        """
        try:
            self.uninstall_dependencies()
            sys.stdout = self.original_stdout
            self.output_buffer.close()
            self.local_namespace.clear()
            self.global_namespace.clear()
        except:
            pass
        finally:
            self._finished = True

    def do_step(
            self,
            actions: List[ActionModel],
            **kwargs) -> Tuple[Observation, float, bool, bool, dict[str, Any]]:
        """
        Step the executor
        Args:
            actions: actions
            **kwargs: -
        Returns:
            Observation, float, bool, bool, dict[str, Any]: -
        """
        self.step_finished = False
        reward = 0
        fail_error = ""
        observation = build_observation(observer=self.name(),
                                        ability=PythonToolAction.EXECUTE.value.name)
        try:
            if not actions:
                return (observation, reward,
                        kwargs.get("terminated",
                                   False), kwargs.get("truncated", False), {
                            "exception": "actions is empty"
                        })
            for action in actions:
                code = action.params.get("code", "")
                if not code:
                    logger.warning(f"{action} no code to execute.")
                    continue
                try:
                    _, output, error = self.execute(code)
                    observation.content = output
                except Exception as e:
                    error = str(e)
                    output = error

                observation.action_result.append(
                    ActionResult(is_done=True,
                                 success=False if error else True,
                                 content=f"{output}",
                                 error=f"{error}",
                                 keep=False))
            reward = 1
        except Exception as e:
            fail_error = str(e)
        finally:
            self._finished = True

        info = {"exception": fail_error}
        info.update(kwargs)
        return (observation, reward, kwargs.get("terminated", False),
                kwargs.get("truncated", False), info)

    def execute(self, code, timeout=300):
        """
        Execute the code
        Args:
            code: python code
            timeout: timeout seconds
        Returns:
            result, output, error
        """
        required_packages = self.extract_imports(code)
        self.install_dependencies(required_packages)
        self.python_repl.globals = self.global_namespace
        self.python_repl.locals = self.local_namespace
        error = None
        try:
            output = self.python_repl.run(code, timeout)
        except Exception as e:
            error = f'{repr(e)}'
        finally:
            self.uninstall_dependencies()
        return '', output, error

    def get_execute_result(self):
        """
        Get the execute result
        Returns:
            output, error
        """
        output = None
        error = ''
        try:
            output = self.output_buffer.getvalue()
            self.output_buffer.truncate(0)
            self.output_buffer.seek(0)
            sys.stdout = self.original_stdout
        except Exception as e:
            error = f'{repr(e)}'
            logger.warning(f"Failed to get output, {repr(e)}")
        return output, error
