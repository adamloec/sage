import click
from sage.server import run as run_server

@click.group()
def cli():
    """Sage CLI tool"""
    pass

@cli.command()
@click.option('--host', default='127.0.0.1', help='The host to bind to')
@click.option('--port', default=8000, help='The port to bind to')
@click.option('--reload/--no-reload', default=False, help='Enable auto-reload')
def serve(host, port, reload):
    """Start the Sage API server"""
    run_server(host=host, port=port, reload=reload)

@cli.command()
def version():
    """Show the current version of Sage"""
    from sage import __version__
    click.echo(f"Sage version: {__version__}")

if __name__ == '__main__':
    cli() 