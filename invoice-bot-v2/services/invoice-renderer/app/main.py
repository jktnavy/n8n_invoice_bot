from fastapi import FastAPI

from app.renderer import render_invoice_pdf
from app.schemas import RenderInvoiceRequest, RenderInvoiceResponse

app = FastAPI(title="STA Invoice Renderer", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/render/invoice", response_model=RenderInvoiceResponse)
def render_invoice(request: RenderInvoiceRequest) -> RenderInvoiceResponse:
    file_path, digest, size = render_invoice_pdf(request.invoice)
    return RenderInvoiceResponse(ok=True, file_path=str(file_path), sha256=digest, size=size)

