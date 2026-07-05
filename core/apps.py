from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.conf import settings

        if settings.LSTM_BACKEND != 'keras':
            return

        from core.ml import runtime

        try:
            from ml_models.inference import load_model, predict_sentiment

            load_model()
            predict_sentiment("warmup", verbose=False)
            runtime.IS_READY = True
            runtime.STARTUP_ERROR = None
        except Exception as exc:
            runtime.IS_READY = False
            runtime.STARTUP_ERROR = str(exc)
