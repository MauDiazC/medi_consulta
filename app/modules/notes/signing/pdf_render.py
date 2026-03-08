from weasyprint import HTML


def render_snapshot_pdf(snapshot):
    html_text = f"""
    <html><body>
    <h1>Clinical Snapshot</h1>
    <pre>{snapshot.snapshot_json}</pre>
    <hr/>
    <p><strong>SHA256:</strong> {snapshot.content_hash}</p>
    <p><strong>Signature:</strong> {snapshot.signature}</p>
    <p><strong>Signer:</strong> {snapshot.signed_by}</p>
    </body></html>
    """

    pdf_bytes = HTML(string=html_text).write_pdf()
    return pdf_bytes