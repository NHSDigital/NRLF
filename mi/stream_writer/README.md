## Resubmitting the event

If you ever find yourself in a situation where the stream-writer has failed - it will put the event into an S3 Bucket called mi-errors

The way top resubmit the file is to take just the Records section of the file:

```json
{
    "error": "from_document_pointer() missing 1 required positional argument: 'custodian'",
    "error_type": "TypeError",
    "function": "mi.stream_writer.index._handler",
    "trace": "Traceback (most recent call last):\n  File \"/var/task/mi/stream_writer/event_handling.py\", line 36, in wrapper\n    response = fn(**kwargs)\n  File \"/var/task/mi/stream_writer/index.py\", line 67, in _handler\n    record_params = RecordParams.from_document_pointer(**document_pointer)\nTypeError: from_document_pointer() missing 1 required positional argument: 'custodian'\n",
    "status": "ERROR",
    "metadata": {
        "event": {
            "Records": [{"there will be data here"}] // <--- copy everything in this section
        }
    }
}
```

Solve the error that has been presented above, and then you can invoke the stream_writer lambda for that environment with the new event - below is what you would enter:

```json
{
  "Records": [{"there will be data here"}]
}
```

Then you can invoke the lambda and it will be a replica (with any changes required to ensure it passes) of the original event
