import collections.abc as col
import io
import typing as tp


if tp.TYPE_CHECKING:
    from _typeshed import WriteableBuffer


class StreamAdapter(io.RawIOBase):
    """
    Convierte un iterable de bytes en un objeto de flujo de datos.

    Optimizado para consumo de bajo nivel mediante readinto.
    Esto permite usar un generador de bytes como una fuente de datos
    legible por funciones que esperan un objeto de tipo io.RawIOBase.

    Parameters
    ----------
    iterable : col.Iterable[bytes]
        Un iterable que produce fragmentos de bytes.

    Attributes
    ----------
    iterator : Iterator[bytes]
        Un iterador sobre el iterable de bytes.
    buffer : bytes
        Un buffer interno para almacenar bytes no leídos.
    _closed : bool
        Indica si el stream ha sido cerrado.

    Methods
    -------
    readable() -> bool
        Indica si el stream es legible.
    readinto(buffer: WriteableBuffer) -> int
        Lee bytes en el buffer proporcionado.
    """

    def __init__(self, iterable: col.Iterable[bytes]) -> None:
        self.iterator = iter(iterable)
        self.buffer = b""
        self._closed = False

    def __repr__(self) -> str:
        return f"StreamAdapter ({self.iterator!r})>"

    def readable(self) -> bool:
        """
        Indica que el stream es legible.

        Returns
        -------
        bool
            True si el stream está abierto y legible, False si está
            cerrado.
        """
        return not self._closed

    def close(self) -> None:
        """Cierra el stream y libera el iterador."""
        if not self._closed:
            self._closed = True
            self.iterator = iter([])
            self.buffer = b""
            super().close()

    def readinto(self, buffer: "WriteableBuffer") -> int:
        """
        Lee bytes y los escribe en un buffer.

        Lee bytes directamente hacia un buffer pre-asignado.
        Esta es la base de la eficiencia en io.BufferedReader.

        Parameters
        ----------
        buffer : WriteableBuffer
            Un buffer pre-asignado donde se escribirán los bytes leídos.

        Returns
        -------
        int
            El número de bytes leídos y escritos en el buffer.

        Raises
        ------
        ValueError
            Si el stream está cerrado.
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")

        # Realiza la lectura en el buffer proporcionado
        return self._do_read(buffer)

    def _do_read(self, buffer: col.Buffer) -> int:
        view = memoryview(buffer).cast("B")
        bytes_read = 0

        # Intentamos llenar el buffer solicitado tanto como sea posible
        while bytes_read < view.nbytes:
            # 1. Si el buffer interno está vacío, buscamos el siguiente
            #    chunk válido
            if not self.buffer:
                try:
                    chunk = next(self.iterator)
                    # Saltamos chunks vacíos para evitar bucles de
                    # longitud cero
                    while not chunk:
                        chunk = next(self.iterator)
                    self.buffer = chunk
                except StopIteration:
                    # No hay más datos en el iterador
                    break

            # 2. Calculamos cuánto del chunk actual cabe en el espacio
            #    restante
            remaining_space = view.nbytes - bytes_read
            n = min(len(self.buffer), remaining_space)

            # 3. Copiamos y actualizamos punteros
            view[bytes_read : bytes_read + n] = self.buffer[:n]
            self.buffer = self.buffer[n:]
            bytes_read += n

        return bytes_read


__all__ = ["StreamAdapter"]
