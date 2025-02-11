import click
from sage.server import run as run_server

@click.group()
def cli():
    """Sage CLI tool"""
    pass

@cli.command()
@click.option('--host', default='0.0.0.0', help='The host to bind to')
@click.option('--port', default=8000, help='The port to bind to')
@click.option('--reload/--no-reload', default=False, help='Enable auto-reload')
@click.option('--mode', 
              type=click.Choice(['production', 'standalone']), 
              default=None, 
              help='Run the server in the specified mode. If not provided, defaults to the value in sage/config.py')
def serve(host, port, reload, mode):
    """Start the Sage API server"""
    # If a mode is specified, override the default mode in the config
    if mode is not None:
        import sage.config as config
        config.MODE = mode
        click.echo(f"Running in {mode} mode")
    
    run_server(host=host, port=port, reload=reload)

@cli.command()
def version():
    """Show the current version of Sage"""
    from sage import __version__
    click.echo(f"Sage version: {__version__}")

if __name__ == '__main__':
    cli() 