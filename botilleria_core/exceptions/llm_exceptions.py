class LLMProviderError(Exception):
    """Excepción lanzada cuando falla el proveedor de LLM (ej. OpenRouter, LiteLLM) o hay timeout."""

    def __init__(self, message: str = "Error de comunicación con el proveedor del LLM"):
        self.message = message
        super().__init__(self.message)
