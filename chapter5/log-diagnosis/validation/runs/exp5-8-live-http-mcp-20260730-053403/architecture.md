# Live diagnosis experiment architecture

The orchestrator calls a local HTTP order service. Refund flows MUST call
`verify_refund_eligibility` before `process_refund`. Inventory origin calls
have a 250 ms client deadline; on timeout the orchestrator MUST call the same
`check_stock` operation through the degraded cache route and finish normally.
Every trajectory turn records its measured HTTP latency and raw response.
