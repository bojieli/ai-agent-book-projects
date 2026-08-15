import click


@click.group()
def main(*args, **kwargs):
    print(
        """\
    AWorld CLI Help:
        aworld web: run aworld web ui server
        aworld api: run aworld api server
        aworld help: show help"""
    )


@main.command("web")
@click.option(
    "--port", type=int, default=8000, help="Port to run the AWorld api server"
)
@click.argument("args", nargs=-1)
def main_web(port, args=None, **kwargs):
    from .web import web_server

    web_server.run_server(port, args, **kwargs)


@main.command("api")
@click.option(
    "--port", type=int, default=8000, help="Port to run the AWorld api server"
)
@click.argument("args", nargs=-1)
def main_api(port, args=None, **kwargs):
    from .web import api_server

    api_server.run_server(port, args, **kwargs)


if __name__ == "__main__":
    main()
