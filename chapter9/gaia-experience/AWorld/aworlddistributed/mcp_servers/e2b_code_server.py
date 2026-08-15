from e2b_code_interpreter import Sandbox
from pydantic import Field
from mcp.server.fastmcp import FastMCP
import os

# Initialize MCP server
mcp = FastMCP("e2b-code-server")


@mcp.tool(description="Upload local file to e2b sandbox.")
async def e2b_upload_file(
    path: str = Field(
        description="The local file path to upload."
    )
) -> str:
    """
    Upload local file to e2b sandbox.

    Args:
        path (str): The local file path to upload.

    Returns:
        str: E2b file path and sandbox_id.

    """
    try:
        os.environ["E2B_API_KEY"] = os.getenv("E2B_API_KEY")
        sbx = Sandbox()
        local_file_name = os.path.basename(path)
        e2b_file_path = f"/home/user/{local_file_name}"
        # Read local file relative to the current working directory
        with open(path, "rb") as file:
        # Upload file to the sandbox to absolute path
            sbx.files.write(e2b_file_path, file)
        return f"{e2b_file_path}, {sbx.sandbox_id}"
    except Exception as e:
        return f"Upload failed. Error: {str(e)}"


@mcp.tool(description="Run code in a specified e2b sandbox.")
async def e2b_run_code(
    sandbox_id: str = Field(
        default=None,
        description="The sandbox id to run code in, if you have uploaded a file, you should use the sandbox_id returned by the e2b_upload_file function."
    ),
    code_block: str = Field(
        default=None,
        description="The code block to run in e2b sandbox."
    ),
) -> str:
    """
    Run code in a specified e2b sandbox.

    Args:
        sandbox_id (str): The sandbox id to run code in.
        code_block (str): The code block to run in e2b sandbox.

    Returns:
        str: The result of running the code block.
    """
    try:
        os.environ["E2B_API_KEY"] = os.getenv("E2B_API_KEY")
        sbx = Sandbox(
            sandbox_id=sandbox_id,
        )
        execution = sbx.run_code(code_block)
        return execution.logs
    except Exception as e:
        return f"Run code failed. Error: {str(e)}"

def main():
    from dotenv import load_dotenv
    load_dotenv()

    import sys
    print("Starting E2b Code MCP Server...", file=sys.stderr)
    mcp.run(transport='stdio')


# Make the module callable
def __call__():
    """
    Make the module callable for uvx.
    This function is called when the module is executed directly.
    """
    main()


# Add this for compatibility with uvx
import sys
sys.modules[__name__].__call__ = __call__

# Run the server when the script is executed directly
if __name__ == "__main__":
    main()

