from dishka import AsyncContainer, Provider, make_async_container
from dishka.integrations.fastapi import FastapiProvider


def make_service_container(*providers: Provider) -> AsyncContainer:
    """Build a FastAPI Dishka container from configured providers."""
    return make_async_container(FastapiProvider(), *providers)
