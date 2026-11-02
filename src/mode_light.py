"""Confirmación breve mediante la última tecla física recordada por el CH57x."""
import threading


class ModeLight:
    def __init__(self, write, preference, lock, timer_factory=threading.Timer):
        self.write = write
        self.preference = preference
        self.lock = lock
        self.timer_factory = timer_factory
        self.timer = None
        self.generation = 0

    def cancel(self):
        # También se usa antes de una escritura manual o de preparar el teclado.
        with self.lock:
            self.generation += 1
            if self.timer:
                self.timer.cancel()
                self.timer = None

    def pulse(self):
        with self.lock:
            self.cancel()
            # En Al pulsar la propia tecla ya produce la confirmación.
            if self.preference() == 1:
                return
            try:
                result = self.write(1)
                if not result.get("sent"):
                    return
            except OSError:
                # Si una secuencia USB falla a medias, intentar restaurar también.
                self._restore(self.generation)
                return
            generation = self.generation
            self.timer = self.timer_factory(0.45, lambda: self._restore(generation))
            self.timer.daemon = True
            self.timer.start()

    def _restore(self, generation):
        with self.lock:
            if generation != self.generation:
                return
            self.timer = None
            try:
                self.write(self.preference())
            except OSError:
                pass  # Desconectar el teclado no puede detener el motor.

    def close(self):
        with self.lock:
            pending = self.timer is not None
            self.cancel()
            if pending:
                self._restore(self.generation)
