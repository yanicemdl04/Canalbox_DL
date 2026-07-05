def lstm_status(request):
    from core.ml.runtime import IS_READY, STARTUP_ERROR

    return {
        "lstm_ready": IS_READY,
        "lstm_error": STARTUP_ERROR,
    }
