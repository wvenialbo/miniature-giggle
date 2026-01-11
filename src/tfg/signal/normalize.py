import numpy as np
import numpy.typing as npt
import scipy as sp


def normalize_by_envelope(
    timeseries: npt.ArrayLike, epsilon: float = 1e-9
) -> npt.NDArray[np.float64]:
    """
    Elimina el efecto de atenuación (damping) usando la envolvente de Hilbert.
    """
    # Calcular la señal analítica
    analitics = sp.signal.hilbert(timeseries)
    envelope = np.abs(analitics)

    # Evitar división por cero en señales que mueren completamente
    envelope[envelope < epsilon] = epsilon

    # Señal con amplitud constante
    result = timeseries / envelope

    return result.astype(np.float64).view(np.ndarray)
