import contextlib
import locale
import os
import typing as tp
import warnings

import numpy as np
import numpy.typing as npt
import scipy as sp


# ----------------------------------------------------------------------

import goesdl.gridsat

filter = goesdl.gridsat.GridSatProductLocatorGC(scene="F", origins="G12", versions="v01")

print(filter)
print(filter.get_base_url("HTTP"))
# filter.get_datetime("HTTP")
# filter.get_paths("HTTP")
filter.match("HTTP")
help(filter)

# ----------------------------------------------------------------------

filter = goesdl.gridsat.GridSatProductLocatorB1(versions="v02r01")
# filter.get_base_url("")

# ----------------------------------------------------------------------

LangType = tp.Literal["en", "es"]

SUPPORTED_LANG = set(tp.get_args(LangType))


def _get_lang(lang_param: str | None) -> str:
    """
    Determina el idioma para mostrar la ayuda según la precedencia
    establecida.

    Parameters
    ----------
    lang_param : str | None
        Idioma proporcionado explícitamente ('en' o 'es'). Si es None, se
        intentará detectar el idioma automáticamente.

    Returns
    -------
    str
        El idioma seleccionado ('en' o 'es').

    Raises
    ------
    ValueError
        Si el parámetro `lang_param` no es None, y no es 'en' ni 'es'.
    """
    # 1. Verificar el parámetro lang
    if lang_param is not None:
        if lang_param not in SUPPORTED_LANG:
            raise ValueError(
                f"El idioma '{lang_param}' no es válido. "
                "Use 'en' para inglés o 'es' para español."
            )
        print(f"Idioma seleccionado por parámetro: {lang_param}")
        return lang_param

    # 2. Verificar la variable de entorno GOESDL_LANG
    if env_lang := os.environ.get("GOESDL_LANG"):
        env_lang = env_lang.strip().lower()
        if env_lang in SUPPORTED_LANG:
            print(f"Idioma seleccionado por variable de entorno: {env_lang}")
            return env_lang

        # Si la variable existe pero tiene un valor no válido,
        # ¿continuamos con el siguiente método o notificamos de la configuración incorrecta?

    # 3. Intentar detectar el idioma del sistema operativo

    with contextlib.suppress(Exception):
        sys_lang, _ = locale.getdefaultlocale()
        if sys_lang:
            lang_code = sys_lang.split("_")[0].lower()
            if lang_code in SUPPORTED_LANG:
                print(f"Idioma detectado del sistema operativo: {lang_code}")
                return lang_code

    # 4. Por defecto: inglés
    return "en"


# Función de prueba para verificar el comportamiento
def test_lang_selection() -> None:
    """Función para probar la selección de idioma"""
    print("=== Pruebas de selección de idioma ===")

    # Guardar estado original de variables de entorno
    original_env = os.environ.get("GOESDL_LANG")

    # Test 1: Parámetro explícito
    print("\n1. Con parámetro 'es':")
    print(f"   Resultado: {_get_lang('es')}")

    # Test 2: Parámetro 'en'
    print("\n2. Con parámetro 'en':")
    print(f"   Resultado: {_get_lang('en')}")

    # Test 3: Variable de entorno
    print("\n3. Con variable GOESDL_LANG='es':")
    os.environ["GOESDL_LANG"] = "es"
    print(f"   Resultado: {_get_lang(None)}")

    # Test 4: Parámetro inválido
    print("\n4. Con parámetro inválido 'fr':")
    try:
        _get_lang("fr")
    except ValueError as e:
        print(f"   Excepción: {e}")

    # Restaurar variable de entorno
    if original_env:
        os.environ["GOESDL_LANG"] = original_env
    else:
        del os.environ["GOESDL_LANG"]

    print("\n=== Fin de pruebas ===")


def _check_is_fitted(self: tp.Any, attributes: list[str]) -> None:
    for attr in attributes:
        if not hasattr(self, attr):
            raise ValueError(f"El estimador no ha sido ajustado con {attr}")


def find_parabolic_vertex_np1v(
    y: npt.ArrayLike,
    x: npt.ArrayLike,
    k: int | np.intp | npt.ArrayLike,
    eps: float | np.floating = 1e-10,
) -> npt.NDArray[np.float64]:
    """
    Refina picos en múltiples curvas con interpolación parabólica.

    Para cada una de las `m` curvas, ajusta una parábola a tres puntos
    adyacentes alrededor del índice correspondiente en `k` y devuelve
    las coordenadas del vértice. Permite refinar simultáneamente un pico
    por curva, siendo útil en procesamiento por lotes de señales.

    Es una generalización bidimensional de `find_parabolic_vertex_1p1v`,
    diseñada para operar de forma vectorizada sobre múltiples curvas y
    un índice por curva.

    Parameters
    ----------
    y : ArrayLike
        Valores de las curvas. Puede ser un array unidimensional (n,)
        para una sola curva, o bidimensional (m, n) para m curvas.
    x : ArrayLike
        Posiciones correspondientes. Puede ser (n,) (las mismas para
        todas las curvas) o (m, n) (posiciones específicas por curva).
    k : int | np.intp | ArrayLike
        Índice o array de índices de los candidatos a pico. Si es un
        entero, se replica para todas las curvas. Debe tener longitud m
        (un índice por curva) y valores enteros en [0, n-1].
    eps : float | np.floating, optional
        Umbral para detectar parábolas degeneradas (denominador ~0).
        Por defecto es 1e-10.

    Returns
    -------
    NDArray[np.float64]
        Array de forma (m, 2). La columna 0 son las posiciones x
        refinadas, la columna 1 los valores y refinados. Si un índice
        está en un borde o la parábola es degenerada, se devuelven las
        coordenadas originales de ese punto.

    Raises
    ------
    ValueError
        Si `eps` no es positivo, si `x` e `y` no tienen formas
        compatibles, si `k` no tiene longitud m, si hay índices fuera de
        rango o si hay menos de tres puntos por curva.
    TypeError
        Si `k` no es un entero o un array de enteros.

    Examples
    --------
    >>> import numpy as np
    >>> # Una sola curva, un solo pico
    >>> x = np.arange(10, dtype=float)
    >>> y = np.array([0, 1, 3, 6, 9, 10, 8, 5, 2, 0])
    >>> find_parabolic_vertex_np1v(y, x, 5)
    array([[4.9, 10.05]])
    >>> # Tres curvas, un pico por curva
    >>> y3 = np.vstack([y, y+2, y-1])
    >>> find_parabolic_vertex_np1v(y3, x, [5, 5, 5])
    array([[4.9       , 10.05      ],
           [4.9       , 12.05      ],
           [4.9       ,  9.05      ]])
    >>> # Posiciones x distintas para cada curva
    >>> x3 = np.vstack([x, x*1.1, x*0.9])
    >>> find_parabolic_vertex_np1v(y3, x3, [5, 5, 5])
    array([[4.9       , 10.05      ],
           [5.39      , 12.05      ],
           [4.41      ,  9.05      ]])

    Notes
    -----
    **Notas de diseño**

    1. **Generalización a múltiples curvas**:
        La función extiende la interpolación parabólica al caso de
        múltiples curvas (array 2D). Cada curva se procesa de manera
        independiente pero vectorizada, lo que ofrece un alto
        rendimiento en procesamiento por lotes.

    2. **Flexibilidad en las posiciones x**:
        - Si `x` es unidimensional, se asume que todas las curvas
          comparten las mismas posiciones muestrales.
        - Si `x` es bidimensional con una sola fila (1, n) y hay
          múltiples curvas, se replica esa fila para todas las curvas.
        - Si `x` es bidimensional (m, n), cada curva tiene sus propias
          posiciones.

    3. **Índices de pico**:
        - Si `k` es un entero, se interpreta como el mismo índice para
          todas las curvas y se replica automáticamente.
        - Si `k` es un array, debe tener un elemento por curva (m).

    4. **Variables principales**:
        - `j`: Array de índices de fila (0..m-1) que permite indexar
          cada curva junto con su índice de pico `k`.
        - `y_1`: Valores de las curvas en los índices `k`. Representa la
          estimación inicial de cada pico.
        - `y_0`, `y_2`: Valores en los puntos adyacentes. Se inicializan
          con `np.nan` y se completan solo donde existen puntos vecinos.
        - `denominador`: Diferencia segunda `y₀ - 2y₁ + y₂`.
          Proporcional a la curvatura de la parábola en cada punto.
        - `numerador`: Semidiferencia `0.5*(y₀ - y₂)`. Estimación de la
          pendiente en el entorno de cada punto central.
        - `delta_x`, `delta_y`: Desplazamientos sub‑muestra desde el
          punto central al vértice de la parábola.
        - `bad_mask`: Máscara que identifica los casos donde no se puede
          interpolar (bordes o parábolas degeneradas). En esos casos el
          resultado se reemplaza por las coordenadas originales.

    5. **Validaciones exhaustivas**:
        Se comprueban las formas de `x` e `y`, la longitud de `k`, los
        rangos de los índices y la cantidad mínima de puntos. Esto
        asegura que la función sea robusta en contextos académicos.

    6. **Eficiencia vectorizada**:
        Todas las operaciones se realizan con operaciones de NumPy,
        evitando bucles Python. El uso de máscaras booleanas permite
        manejar eficientemente los bordes sin romper la vectorización.
    """
    # ------------------------------------------------------------------
    # Validación de parámetros escalares
    # ------------------------------------------------------------------
    # eps debe ser positivo para detectar parábolas degeneradas.
    eps = float(eps)
    if eps <= 0:
        raise ValueError("eps debe ser positivo")

    # Convertir k a un array de enteros, admitiendo escalar.
    # Un escalar se interpreta como el mismo índice para todas las
    # curvas y se replica más adelante.
    if isinstance(k, int):
        k = [k]

    k = np.asarray(k)

    # Asegurar que todos los valores de k sean enteros; evita
    # truncamientos silenciosos de flotantes.
    if not np.issubdtype(k.dtype, np.integer):
        raise TypeError("k debe contener únicamente valores enteros")

    k = k.astype(np.intp)

    # k debe ser unidimensional; un array multidimensional complicaría
    # la indexación posterior.
    if k.ndim != 1:
        raise ValueError("k debe ser un array unidimensional (m,).")

    # ------------------------------------------------------------------
    # Validación y preparación de las curvas y sus posiciones
    # ------------------------------------------------------------------
    # Garantizar que x e y sean arrays de flotantes de 64 bits para
    # precisión en los cálculos algebraicos.
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    # Si y es unidimensional, se trata como una sola curva y se
    # convierte a bidimensional (1, n) para unificar el tratamiento.
    if y.ndim == 1:
        y = y[np.newaxis, :]

    # La función está diseñada para múltiples curvas.
    if y.ndim != 2:
        raise ValueError(
            "y debe ser un array unidimensional (n,) o "
            "bidimensional (m, n)."
        )

    m, n = y.shape

    # Si no hay curvas (m=0), se devuelve un array vacío.
    if k.size == 0:
        return np.empty((m, 2), dtype=np.float64)

    # Si k tiene un solo elemento, se replica para todas las curvas.
    # Esto permite usar un índice común para todas las curvas.
    if k.size == 1:
        k = np.tile(k.ravel(), (m,))

    # k debe tener un elemento por curva.
    if k.size != m:
        raise ValueError(
            f"k debe tener longitud m={m}, pero tiene longitud {k.size}"
        )

    # Todos los índices deben estar dentro del rango válido.
    if np.any(k < 0) or np.any(k >= n):
        raise IndexError(
            f"Todos los índices en k deben estar entre 0 y {n - 1}"
        )

    # Adaptar las posiciones x según su dimensionalidad:
    # - Si x es unidimensional, se asume que todas las curvas comparten
    #   las mismas posiciones.
    # - Si x tiene una sola fila (1, n) y hay múltiples curvas, se
    #   replica esa fila.
    # - Si x ya es (m, n), se usa directamente.
    if x.ndim == 1 or (x.shape[0] == 1 and m != 1):
        x = np.tile(x.ravel(), (m, 1))

    # x debe ser bidimensional después de la adaptación.
    if x.ndim != 2:
        raise ValueError(
            "x debe ser un array unidimensional (n,) o "
            "bidimensional (m, n) o (1, n)."
        )

    # Verificar coherencia entre las formas de x e y.
    if x.shape[1] != y.shape[1]:
        raise ValueError("x e y deben tener la misma cantidad de valores (n)")

    if x.shape[0] != y.shape[0]:
        raise ValueError("x e y deben tener la misma forma (m, n)")

    # Se requieren al menos tres puntos por curva para definir una
    # parábola.
    if x.shape[1] < 3:
        raise ValueError("Se requieren al menos 3 puntos para interpolación")

    # ------------------------------------------------------------------
    # Índices de fila para cada curva
    # ------------------------------------------------------------------
    # j permite indexar cada curva junto con su índice de pico k.
    j = np.arange(m, dtype=np.intp)

    # ------------------------------------------------------------------
    # Obtención de los tres puntos para cada curva
    # ------------------------------------------------------------------
    # Punto central: coordenada x y valor de cada curva en su índice k.
    x_1 = x[j, k]
    y_1 = y[j, k]

    # Inicializar los puntos laterales con NaN. Se sobreescribirán solo
    # donde exista un punto adyacente válido.
    y_0 = np.full(k.shape, np.nan, dtype=np.float64)
    y_2 = y_0.copy()

    # Máscara de índices que tienen un punto anterior (k >= 1).
    mask_0 = k >= 1
    y_0[mask_0] = y[j[mask_0], k[mask_0] - 1]

    # Máscara de índices que tienen un punto posterior (k <= n-2).
    mask_2 = k <= n - 2
    y_2[mask_2] = y[j[mask_2], k[mask_2] + 1]

    # ------------------------------------------------------------------
    # Cálculo de los parámetros de la parábola
    # ------------------------------------------------------------------
    # El denominador es proporcional a la curvatura. Valores cercanos a
    # cero indican una parábola degenerada (casi lineal).
    denominator = y_0 - 2.0 * y_1 + y_2
    numerator = 0.5 * (y_0 - y_2)

    # Identificación de casos donde la interpolación no es posible:
    # 1. Índices en los bordes (no tienen ambos puntos adyacentes).
    # 2. Parábolas con curvatura despreciable (|denominador| < eps).
    is_at_edge = (k == 0) | (k == n - 1)
    is_flat = np.abs(denominator) < eps
    bad_mask = is_at_edge | is_flat

    # Desplazamientos sub‑muestra desde el punto central hasta el
    # vértice.
    delta_x = numerator / denominator
    delta_y = -0.5 * numerator * delta_x

    # Coordenadas refinadas del vértice.
    x_vertex = x_1 + delta_x
    y_vertex = y_1 + delta_y

    # ------------------------------------------------------------------
    # Sustitución de los casos no interpolables
    # ------------------------------------------------------------------
    # Donde la interpolación falla (bordes o parábolas planas) se
    # devuelve el punto original.
    x_vertex[bad_mask] = x_1[bad_mask]
    y_vertex[bad_mask] = y_1[bad_mask]

    # ------------------------------------------------------------------
    # Formato de salida
    # ------------------------------------------------------------------
    # Apilar las coordenadas x e y en un array de dos columnas.
    return np.column_stack([x_vertex, y_vertex])


def normalize_by_envelope(
    timeseries: npt.ArrayLike,
    epsilon: float = 1e-9,
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


class ButterworthFilter:

    FILTER_MODES = {"lowpass", "highpass", "bandpass", "bandstop"}

    def __init__(
        self,
        sampling_rate: float,
        order: int = 4,
        mode: tp.Literal[
            "lowpass", "highpass", "bandpass", "bandstop"
        ] = "bandpass",
        analog: bool = False,
    ) -> None:
        if sampling_rate <= 0:
            raise ValueError(
                "La tasa de muestreo, `sampling_rate`, debe ser "
                f"un número positivo, recibido: {sampling_rate}"
            )
        if order <= 0:
            raise ValueError(
                "El orden del filtro, `order`, debe ser un número positivo, "
                f"recibido: {order}"
            )
        if mode not in self.FILTER_MODES:
            modes = "', '".join(sorted(self.FILTER_MODES))
            raise ValueError(
                "El modo del filtro, `mode`, debe ser uno de los siguientes: "
                f"{modes}, recibido: {mode}"
            )

        self.sampling_rate = sampling_rate
        self.order = order
        self.mode = mode
        self.analog = analog

    def get_frecuency(
        self, which: tp.Literal["central", "middle"] = "central"
    ) -> float:
        _check_is_fitted(self, ["frec_main_", "frec_central_", "frec_cutoff_"])

        if which == "central":
            return self.frec_central_

        if which == "middle":
            return self.frec_middle_

        raise ValueError(
            "El parámetro 'which' debe ser 'central' o 'middle', "
            f"recibido: {which}"
        )

    def get_cutoff_frequency(self) -> tuple[float, float]:
        _check_is_fitted(self, ["frec_cutoff_"])

        return self.frec_cutoff_

    def set_cutoff_frequency(
        self, freq_cutoff: tuple[float, float] | float
    ) -> None:
        nyquist = 0.5 * self.sampling_rate

        if isinstance(freq_cutoff, tuple):
            supported_modes = {"bandpass", "bandstop"}
            freq_low, freq_high = sorted(freq_cutoff)
            freq_low, freq_high = freq_low / nyquist, freq_high / nyquist
            freq_error = freq_low <= 0 or freq_high >= 1
            mode_error = self.mode not in supported_modes
            mode_type = "tuple"
            normal_cutoff = freq_low, freq_high
            freq_c = 0.5 * (freq_low + freq_high)
            freq_m = 1.0 / (0.5 * (1.0 / freq_low + 1.0 / freq_high))

        else:
            supported_modes = {"lowpass", "highpass"}
            freq_cut = freq_cutoff / nyquist
            freq_error = freq_cut <= 0 or freq_cut >= 1
            mode_error = self.mode not in supported_modes
            mode_type = "float"
            normal_cutoff = freq_cut, freq_cut
            freq_c = freq_cut
            freq_m = freq_cut

        if freq_error:
            raise ValueError(
                "Cada frequencia de corte, `freq_cutoff` debe estar "
                f"entre 0 y la frecuencia de Nyquist ({nyquist}), "
                f"recibido: {freq_cutoff}"
            )

        if mode_error:
            modes = "' y '".join(supported_modes)
            raise ValueError(
                f"Los modos '{modes}' requieren que `freq_cutoff` "
                f"sea de tipo `{mode_type}`"
            )

        self.frec_cutoff_ = normal_cutoff
        self.frec_central_ = freq_c
        self.frec_middle_ = freq_m

    def set_cutoff_range(
        self, center: float, bandwidth: float, is_period: bool = False
    ) -> None:
        begin = center - bandwidth
        end = center + bandwidth

        if is_period:
            freq_cutoff = 1.0 / end, 1.0 / begin
            freq_c = None
            freq_m = 1.0 / center
        else:
            freq_cutoff = begin, end
            freq_c = center
            freq_m = None

        self.set_cutoff_frequency(freq_cutoff)

        self.frec_central_ = freq_c or self.frec_central_
        self.frec_middle_ = freq_m or self.frec_middle_

    def filter(
        self,
        timeseries: npt.NDArray[np.floating],
    ) -> npt.NDArray[np.float64]:
        _check_is_fitted(self, ["frec_cutoff_"])

        b, a = sp.signal.butter(
            self.order, self.frec_cutoff_, btype=self.mode, analog=self.analog
        )

        return sp.signal.filtfilt(b, a, np.nan_to_num(timeseries, nan=0.0))


class SignalAligner:

    def __init__(
        self,
        filter: ButterworthFilter,
        normalize: bool = False,
        method: tp.Literal[
            "correlation", "fourier", "hilbert"
        ] = "correlation",
        select_frequency: tp.Literal[
            "central", "middle", "dominant", "weighted", "auto"
        ] = "auto",
        select_reference: tp.Literal[
            "variance", "power", "manual"
        ] = "variance",
        eps: float = 1e-10,
    ) -> None:
        self.filter = filter
        self.normalize = normalize
        self.method = method
        self.select_frequency = select_frequency
        self.select_reference = select_reference
        self.eps = eps

        self.reference_index: int | None = None

    def align(self, timeseries: npt.ArrayLike) -> None:
        timeseries = np.asarray(timeseries, dtype=np.float64)

        # 1. Apply band-pass filter and a envelope normalization
        #    to all signals before delay estimation and FFT
        processed_signals = self._preprocess_signal(timeseries)

        # 2. Estimate time delays using the pre-filtered signal
        delays = self._estimate_delays(processed_signals)

        self.delays_ = delays.ravel()

        # 3. Calculate FFT of each signal and generate the frequency
        #    vector
        self._correct_phase(timeseries, delays)

    def _correct_phase(
        self,
        timeseries: npt.NDArray[np.float64],
        delays: npt.NDArray[np.float64],
    ) -> None:
        n_samples = timeseries.shape[1]

        fft = sp.fft.rfft(timeseries)

        fft_frequencies = sp.fft.rfftfreq(
            n_samples, d=1 / self.filter.sampling_rate
        )

        # 4. Apply phase correction and average coherently

        # Phase correction factor: e^(j * 2 * pi * f * tau_i)
        phase_correction = np.exp(1j * 2 * np.pi * fft_frequencies * delays)

        # Apply phase correction
        fft_aligned = fft * phase_correction

        # Calculate the coherent average
        fft_average = fft_aligned.mean(axis=0)

        self.fft_ = fft
        self.fft_aligned_ = fft_aligned
        self.fft_average_ = fft_average
        self.fft_frequencies_ = fft_frequencies
        self.phase_correction_ = phase_correction

        # 5. Calculate the IFFT to reconstruct the aligned signal
        self.signal_ = sp.fft.irfft(fft_average, n=n_samples)

    def _estimate_delays(
        self, processed_signals: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        if self.method == "correlation":
            return self._estimate_delays_corr(processed_signals)

        if self.method == "fourier":
            return self._estimate_delays_fft(processed_signals)

        return self._estimate_delays_hilbert(processed_signals)

    def _estimate_delays_corr(
        self, processed_signals: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        # Number of series
        n_series, n_samples = processed_signals.shape

        n_corrsize = 2 * n_samples - 1

        # Initialize arrays for the correlations and delays
        correlations = np.zeros((n_series - 1, n_corrsize), dtype=np.float64)
        delays = np.zeros((n_series, 1), dtype=np.float64)

        # Get the filtered reference signal
        reference_index = self._select_reference_signal(processed_signals)
        self.reference_index_ = reference_index

        # Create indices array
        all_indices = np.arange(n_series, dtype=np.intp)
        non_reference_indices = all_indices[all_indices != reference_index]

        reference_signal = processed_signals[reference_index]

        # Compute correlations for non-reference signals
        # # correlations[i] --> processed_signals[non_reference_indices[i]]
        for i, k in enumerate(non_reference_indices):
            correlations[i] = sp.signal.correlate(
                processed_signals[k], reference_signal, mode="full"
            )

        # Find peak indices
        peaks = np.argmax(correlations, axis=1)

        # Get lags (same for all correlations)
        lags = sp.signal.correlation_lags(n_samples, n_samples, mode="full")

        # Parabolic interpolation for subsample accuracy
        # Using find_parabolic_vertex_np1v con:
        #   y = correlations (n_series - 1, n_corrsize)
        #   x = lags (n_corrsize,)
        #   k = peaks (n_series - 1,)
        vertices = find_parabolic_vertex_np1v(correlations, lags, peaks)

        # Extract refined lags (in samples)
        lags_refined = vertices[:, 0]

        # Convert to delays in seconds
        delays_times = lags_refined / self.filter.sampling_rate

        # Reshape for phase correction
        delays[non_reference_indices, 0] = delays_times

        return delays.astype(np.float64).view(np.ndarray)

    def _estimate_delays_fft(
        self, processed_signals: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        """
        Estimate time delays using the FFT and the known center frequency
        of the filter.

        This method computes the FFT of each pre‑filtered signal, extracts
        the phase at the filter's center frequency, and converts the phase
        differences to time delays.

        Parameters
        ----------
        processed_signals : NDArray[float64]
            Band‑filtered (and optionally normalized) signals, shape
            (n_series, n_samples).

        Returns
        -------
        delays : NDArray[float64]
            Estimated delays for each signal, shape (n_series, 1), in units
            of the inverse sampling rate.
        """
        n_samples = processed_signals.shape[1]

        # ------------------------------------------------------------------
        # 1. Obtain the filter's center frequency.
        # ------------------------------------------------------------------
        f_center = self._select_alignment_frequency(processed_signals)

        # ------------------------------------------------------------------
        # 2. Compute the FFT of the processed signals.
        # ------------------------------------------------------------------
        # Use rfft because the input is real; the result is complex with
        # shape (n_series, n_freqs), where n_freqs = n_samples//2 + 1.
        fft_signals: npt.NDArray[np.complex64] = sp.fft.rfft(
            processed_signals, axis=1
        )

        # Compute the corresponding frequency vector (in cycles per unit
        # time, same units as sampling_rate).
        fft_freqs: npt.NDArray[np.float64] = sp.fft.rfftfreq(
            n_samples, d=1.0 / self.filter.sampling_rate
        )

        # ------------------------------------------------------------------
        # 3. Find the FFT bin closest to the desired center frequency.
        # ------------------------------------------------------------------
        # The frequency resolution is Δf = sampling_rate / n_samples.
        # We locate the index of the bin whose frequency is nearest to
        # f_center.
        target_idx = np.argmin(np.abs(fft_freqs - f_center))
        actual_freq: np.float64 = fft_freqs[target_idx]

        # ------------------------------------------------------------------
        # 4. Extract the phases at this frequency for every series.
        # ------------------------------------------------------------------
        # The phases are taken from the complex FFT coefficients at the
        # target index. Shape: (n_series,).
        phases = np.angle(fft_signals[:, target_idx])

        # ------------------------------------------------------------------
        # 5. Unwrap the phases across the sensor array.
        # ------------------------------------------------------------------
        # Phase differences between adjacent sensors may exceed π radians,
        # especially for long arrays.  Unwrapping along the sensor axis
        # (axis=0) removes 2π jumps and yields a smooth phase progression.
        # We use np.unwrap with the default period (2π).
        unwrapped_phases = np.unwrap(phases, axis=0)

        # ------------------------------------------------------------------
        # 6. Determine the reference sensor.
        # ------------------------------------------------------------------
        reference_index = self._select_reference_signal(processed_signals)
        self.reference_index_ = reference_index

        # ------------------------------------------------------------------
        # 7. Compute delays from the unwrapped phase differences.
        # ------------------------------------------------------------------
        # For a single frequency, the relation is Δφ = 2π f Δt.
        # Hence Δt = Δφ / (2π f).
        delays_times: npt.NDArray[np.float64] = (
            unwrapped_phases - unwrapped_phases[reference_index]
        ) / (2.0 * np.pi * actual_freq)

        # ------------------------------------------------------------------
        # 8. Reshape to (n_series, 1) for compatibility.
        # ------------------------------------------------------------------
        delays = delays_times.reshape(-1, 1)

        return delays.astype(np.float64)

    def _estimate_delays_hilbert(
        self, processed_signals: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        """
        Estimate time delays using the Hilbert transform and the known center
        frequency of the filter.

        Parameters
        ----------
        processed_signals : NDArray[float64]
            Band‑filtered (and optionally normalized) signals, shape
            (n_series, n_samples).

        Returns
        -------
        delays : NDArray[float64]
            Estimated delays for each signal, shape (n_series, 1), in units
            of the inverse sampling rate (i.e., days if sampling_rate is
            per day).
        """
        n_samples = processed_signals.shape[1]

        # ------------------------------------------------------------------
        # 1. Obtain the filter's center frequency.
        # ------------------------------------------------------------------
        f_center = self._select_alignment_frequency(processed_signals)

        # ------------------------------------------------------------------
        # 2. Compute the analytic signal via the Hilbert transform.
        # ------------------------------------------------------------------
        # sp.signal.hilbert returns the analytic signal, which is complex.
        # The axis parameter allows us to compute the transform for all
        # series at once.
        analytic_signals: npt.NDArray[np.float64] = sp.signal.hilbert(
            processed_signals, axis=1
        )

        # ------------------------------------------------------------------
        # 3. Extract the instantaneous phase and unwrap it along the time
        #    axis for each series.
        # ------------------------------------------------------------------
        # Instantaneous phase: φ(t) = arg( analytic_signal(t) )
        instantaneous_phases = np.angle(analytic_signals)

        # Unwrap each series independently to avoid 2π jumps.
        # np.unwrap operates along the last axis by default, which is
        # the time axis (axis=1). We need to specify axis=1 explicitly
        # for clarity.
        unwrapped_phases = np.unwrap(instantaneous_phases, axis=1)

        # ------------------------------------------------------------------
        # 4. Compute the mean phase for each series, excluding the edges
        #    where the Hilbert transform is less reliable.
        # ------------------------------------------------------------------
        # Discard the first and last quarter of the time window.
        central_start = n_samples // 4
        central_end = 3 * n_samples // 4

        # If the central segment is too short, keep at least 10 samples.
        if central_end - central_start < 10:
            central_start = 0
            central_end = n_samples

        mean_phases = np.mean(
            unwrapped_phases[:, central_start:central_end], axis=1
        )

        # ------------------------------------------------------------------
        # 5. Determine the reference sensor.
        # ------------------------------------------------------------------
        # If a reference index has been set by the user, use it.
        # Otherwise, choose the sensor with the maximum variance in the
        # processed signals (as done in the correlation method).
        reference_index = self._select_reference_signal(processed_signals)
        self.reference_index_ = reference_index

        # ------------------------------------------------------------------
        # 6. Compute delays from the phase differences.
        # ------------------------------------------------------------------
        # For a narrow‑band signal, the relationship between phase
        # difference and time delay is:
        #     Δφ = 2π * f_center * Δt
        # Hence:
        #     Δt = Δφ / (2π * f_center)
        delays_times = (mean_phases - mean_phases[reference_index]) / (
            2.0 * np.pi * f_center
        )

        # ------------------------------------------------------------------
        # 7. Reshape to (n_series, 1) for compatibility with the phase
        #    correction step.
        # ------------------------------------------------------------------
        delays = delays_times.reshape(-1, 1).astype(np.float64)

        return delays

    def _get_dominant_frequency(
        self,
        amplitude_in_band: npt.NDArray[np.float64],
        frequency_in_band: npt.NDArray[np.float64],
    ) -> tuple[float, float, float]:
        """Encuentra la frecuencia con máxima energía dentro de la banda del filtro."""
        mean_amplitude = float(np.mean(amplitude_in_band))
        mean_amplitude = (
            mean_amplitude if mean_amplitude >= self.eps else self.eps
        )

        peak_index = np.argmax(amplitude_in_band)

        peak_amplitude = float(amplitude_in_band[peak_index])
        peak_frequency = float(frequency_in_band[peak_index])

        # Peak-to-Average Ratio
        par = peak_amplitude / mean_amplitude

        return peak_frequency, peak_amplitude, par

    def _get_in_band_fft(
        self, processed_signals: npt.NDArray[np.float64]
    ) -> tuple[
        npt.NDArray[np.float64],
        npt.NDArray[np.float64],
        npt.NDArray[np.float64],
    ]:
        fft_signals: npt.NDArray[np.complex64] = sp.fft.rfft(
            processed_signals, axis=1
        )

        n_samples = processed_signals.shape[1]
        sampling_rate = self.filter.sampling_rate
        fft_freqs: npt.NDArray[np.float64] = sp.fft.rfftfreq(
            n_samples, d=1 / sampling_rate
        )

        lowcut, highcut = self.filter.get_cutoff_frequency()
        band_mask = (fft_freqs >= lowcut) & (fft_freqs <= highcut)
        if not np.any(band_mask):
            band_mask = np.ones_like(fft_freqs, dtype=np.bool_)

        fft_in_band = fft_signals[:, band_mask]
        amp_in_band = np.abs(fft_in_band)

        amplitude_in_band: npt.NDArray[np.float64] = np.mean(
            amp_in_band, axis=0
        )
        power_in_band: npt.NDArray[np.float64] = np.sum(amp_in_band**2, axis=1)

        frequency_in_band: npt.NDArray[np.float64] = fft_freqs[band_mask]

        return amplitude_in_band, frequency_in_band, power_in_band

    def _get_weighted_frequency(
        self,
        amplitude_in_band: npt.NDArray[np.float64],
        frequency_in_band: npt.NDArray[np.float64],
    ) -> tuple[float, bool]:
        """Calcula la frecuencia promedio ponderada."""
        # Ponderada por la amplitud espectral
        sum_amplitude = np.sum(amplitude_in_band)
        flat_fft = bool(sum_amplitude < self.eps)
        sum_amplitude = sum_amplitude if not flat_fft else self.eps

        weighted_frequency = (
            np.sum(frequency_in_band * amplitude_in_band) / sum_amplitude
        )

        return float(weighted_frequency), flat_fft

    def _preprocess_signal(
        self, timeseries: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        # Number of series
        n_series = timeseries.shape[0]

        if n_series <= 1:
            raise ValueError(
                "Se requieren al menos dos series temporales para "
                "realizar la alineación, recibido: "
                f"{n_series}"
            )

        processed_signals = self.filter.filter(timeseries)

        if self.normalize:
            processed_signals = normalize_by_envelope(processed_signals)

        return processed_signals

    def _select_alignment_frequency(
        self, processed_signals: npt.NDArray[np.float64]
    ) -> float:
        """
        Obtiene frecuencia central para alineamiento.

        Parameters
        ----------
        method : str
            "auto": intenta dominante → ponderada → filtro
            "dominant": frecuencia de pico en banda
            "weighted": frecuencia media ponderada
            "filter": frecuencia central del filtro
        """
        method = self.select_frequency

        if method in {"central", "middle"}:
            # Frecuencia central o del periodio medio del filtro
            # - Problema: Asume filtro simétrico y que la señal ocupa
            #   toda la banda.
            warnings.warn(
                f"El método '{method}' no es adecuado para seleccionar la "
                "frecuencia de alineamiento. Se recomienda usar 'auto', "
                "'dominant' o 'weighted'.",
                UserWarning,
            )
            return self.filter.get_frecuency(method)  # type: ignore

        # amplitude_in_band, frequency_in_band, power_in_band
        amplitude_in_band, frequency_in_band, _ = self._get_in_band_fft(
            processed_signals
        )

        if method in {"weighted", "auto"}:
            # Frecuencia media ponderada en banda por amplitud espectral
            # (más robusta para señales multimodales)
            weighted_freq, flat_fft = self._get_weighted_frequency(
                amplitude_in_band, frequency_in_band
            )
            if method == "weighted":
                if flat_fft:
                    warnings.warn(
                        "La FFT en banda es plana, la frecuencia "
                        "ponderada puede no ser representativa.",
                        UserWarning,
                    )
                return weighted_freq
            if not flat_fft:
                return weighted_freq

        if method in {"dominant", "auto"}:
            # Frecuencia dominante en banda (recomendado)
            # - peak_frequency, peak_amplitude, par (Peak-to-Average
            #   Ratio)
            peak_frequency, _, par = self._get_dominant_frequency(
                amplitude_in_band, frequency_in_band
            )
            if method == "dominant":
                if par <= 2.0:
                    warnings.warn(
                        "La calidad de la frecuencia dominante es baja "
                        f"({par:.2f}), considere usar el método "
                        "'auto' o 'weighted' para mayor robustez.",
                        UserWarning,
                    )
                return peak_frequency
            if par > 2.0:
                return peak_frequency

        assert method == "auto"

        return self.filter.get_frecuency("central")

    def _select_reference_signal(
        self, processed_signals: npt.NDArray[np.float64]
    ) -> int:
        method = self.select_reference

        if method == "manual":
            if self.reference_index is None:
                raise ValueError(
                    "El índice de referencia no ha sido establecido. "
                    "Use el método 'set_reference_signal' o cambie el "
                    "método de selección a 'variance' o 'power'."
                )
            warnings.warn(
                "Se está utilizando un índice de referencia manual. "
                "Asegúrese de que este índice sea válido para los datos "
                "actuales.",
                UserWarning,
            )
            return self.reference_index

        if method == "variance":

            # Por varianza (predeterminado)
            # - Ventaja: Simple, rápido, intuitivo (mayor varianza ≈ mayor
            #   SNR).
            # - Problema: Puede elegir sensores con artefactos/outliers que
            #   aumentan varianza sin mejorar SNR.

            signal_variances: npt.NDArray[np.float64] = np.var(
                processed_signals, axis=1
            )
            reference_index = np.argmax(signal_variances)

            return int(reference_index)

        assert method == "power"

        # Máxima potencia en banda (recomendado)
        # - Ventajas:
        #   - Específica para la banda de interés
        #   - Menos sensible a outliers de baja frecuencia
        #   - Correlaciona mejor con SNR real

        # amplitude_in_band, frequency_in_band, power_in_band
        _, _, power_in_band = self._get_in_band_fft(processed_signals)

        reference_index = int(np.argmax(power_in_band))

        return reference_index

    def set_reference_signal(
        self, reference_index: int | np.intp | None = None
    ) -> None:
        self.reference_index = (
            int(reference_index) if reference_index is not None else None
        )


class PropagationAnalyzer:
    """
    Clase para analizar la velocidad de propagación a partir de los delays
    estimados por SignalAligner.
    """

    def __init__(self, signal_aligner: SignalAligner):
        self.signal_aligner = signal_aligner

    def estimate_linear_velocity(self, spacing_km: float) -> dict[str, float]:
        """
        Calcula la velocidad de propagación para sensores en línea recta y equidistantes.

        Parameters
        ----------
        spacing_km : float
            Distancia entre sensores consecutivos en kilómetros.

        Returns
        -------
        dict
            Diccionario con las velocidades en diferentes unidades y métricas de calidad.
        """
        delays = self.signal_aligner.delays_
        n_series = len(delays)

        # Posiciones en km
        positions_km = np.arange(n_series) * spacing_km

        # Regresión lineal: posición = velocidad * delay + c
        # Pero podemos forzar a que pase por el origen (delay=0 en la referencia)
        # Sin embargo, la referencia no necesariamente está en el extremo, así que
        # es mejor hacer regresión con intercepto.

        # Construir matriz de diseño: [delays, unos]
        A = np.vstack([delays, np.ones(n_series)]).T
        # Resolver por mínimos cuadrados
        slope, intercept = np.linalg.lstsq(A, positions_km, rcond=None)[0]

        # La velocidad es la pendiente (km por día si los delays están en días)
        velocity_km_per_day = slope

        # Calcular R^2
        predicted = slope * delays + intercept
        ss_res = np.sum((positions_km - predicted) ** 2)
        ss_tot = np.sum((positions_km - np.mean(positions_km)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 1

        # Convertir a otras unidades
        velocity_km_per_hour = velocity_km_per_day / 24
        velocity_m_per_s = velocity_km_per_day * 1000 / 86400

        # Calcular la velocidad aparente entre sensores consecutivos
        pairwise_velocities = []
        for i in range(n_series - 1):
            delta_pos = spacing_km
            delta_time = delays[i + 1] - delays[i]
            if abs(delta_time) > 1e-10:
                pairwise_velocities.append(delta_pos / delta_time)

        pairwise_velocities = np.array(pairwise_velocities)

        return {
            "velocity_km_per_day": velocity_km_per_day,
            "velocity_km_per_hour": velocity_km_per_hour,
            "velocity_m_per_s": velocity_m_per_s,
            "intercept_km": intercept,
            "R2": r2,
            "pairwise_velocities_mean": (
                np.mean(pairwise_velocities)
                if len(pairwise_velocities) > 0
                else np.nan
            ),
            "pairwise_velocities_std": (
                np.std(pairwise_velocities)
                if len(pairwise_velocities) > 0
                else np.nan
            ),
            "pairwise_velocities": pairwise_velocities,
        }

    def estimate_velocity_with_positions(
        self, positions_km: np.ndarray
    ) -> dict[str, float]:
        """
        Calcula la velocidad de propagación para sensores en posiciones arbitrarias (2D o 3D).

        Parameters
        ----------
        positions_km : np.ndarray
            Array de forma (n_series, n_dim) con las posiciones de los sensores en km.

        Returns
        -------
        dict
            Diccionario con los resultados.
        """
        delays = self.signal_aligner.delays_
        n_series, n_dim = positions_km.shape

        # Ajustar un modelo de plano de onda: delay = (1/v) * (r·n) + t0
        # donde v es la velocidad, n es el vector unitario de dirección, t0 es el tiempo en el origen.
        # Equivalentemente: delay = s · r + t0, donde s = n/v es el vector slowness.

        # Construir matriz de diseño: [x, y, (z), unos]
        A = np.hstack([positions_km, np.ones((n_series, 1))])

        # Resolver por mínimos cuadrados: A @ [sx, sy, (sz), t0] = delays
        params = np.linalg.lstsq(A, delays, rcond=None)[0]

        # Los primeros n_dim componentes son el vector slowness (en días/km)
        slowness_vector = params[:n_dim]
        t0 = params[-1]

        # Calcular la velocidad (magnitud)
        slowness_mag = np.linalg.norm(slowness_vector)
        velocity_km_per_day = 1 / slowness_mag if slowness_mag > 0 else np.inf

        # Calcular el vector unitario de dirección
        if slowness_mag > 0:
            direction_vector = slowness_vector / slowness_mag
        else:
            direction_vector = np.zeros(n_dim)

        # Calcular R^2
        delays_pred = A @ params
        ss_res = np.sum((delays - delays_pred) ** 2)
        ss_tot = np.sum((delays - np.mean(delays)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 1

        # Convertir a otras unidades
        velocity_km_per_hour = velocity_km_per_day / 24
        velocity_m_per_s = velocity_km_per_day * 1000 / 86400

        # Para 2D, calcular el ángulo de propagación (en radianes y grados)
        if n_dim == 2:
            angle_rad = np.arctan2(direction_vector[1], direction_vector[0])
            angle_deg = np.degrees(angle_rad)
        else:
            angle_rad = None
            angle_deg = None

        return {
            "velocity_km_per_day": velocity_km_per_day,
            "velocity_km_per_hour": velocity_km_per_hour,
            "velocity_m_per_s": velocity_m_per_s,
            "slowness_vector": slowness_vector,
            "direction_vector": direction_vector,
            "t0_days": t0,
            "R2": r2,
            "angle_rad": angle_rad,
            "angle_deg": angle_deg,
        }

    def plot_propagation_analysis(
        self,
        spacing_km: float | None = None,
        positions_km: np.ndarray | None = None,
        figsize: tuple[int, int] = (15, 5),
    ):
        """
        Genera gráficos de análisis de propagación.

        Parameters
        ----------
        spacing_km : float, optional
            Distancia entre sensores consecutivos para array lineal.
        positions_km : np.ndarray, optional
            Posiciones de los sensores para análisis 2D/3D.
        figsize : tuple
            Tamaño de la figura.

        Returns
        -------
        fig : matplotlib.figure.Figure
        axes : np.ndarray of matplotlib.axes.Axes
        """
        delays = self.signal_aligner.delays_

        if positions_km is not None:
            # Análisis 2D/3D
            n_dim = positions_km.shape[1]
            if n_dim == 1:
                # Tratar como lineal
                positions_km = positions_km.flatten()
                spacing_km = (
                    np.mean(np.diff(positions_km))
                    if len(positions_km) > 1
                    else 0
                )
                result = self.estimate_linear_velocity(spacing_km)
            else:
                result = self.estimate_velocity_with_positions(positions_km)
        elif spacing_km is not None:
            # Análisis lineal
            result = self.estimate_linear_velocity(spacing_km)
            positions_km = np.arange(len(delays)) * spacing_km
            n_dim = 1
        else:
            raise ValueError("Debe proporcionar spacing_km o positions_km")

        # Crear figura
        if n_dim == 1:
            fig, axes = plt.subplots(1, 3, figsize=figsize)
        else:
            fig, axes = plt.subplots(1, 3, figsize=figsize)

        # Gráfico 1: Delays vs posición (para 1D) o en 2D
        ax = axes[0]
        if n_dim == 1:
            ax.scatter(positions_km, delays, s=100)
            ax.set_xlabel("Posición (km)")
            ax.set_ylabel("Delay (días)")
            ax.set_title("Delays vs Posición")
            # Añadir línea de regresión
            x_fit = np.array([positions_km.min(), positions_km.max()])
            y_fit = result["slope"] * x_fit + result["intercept_km"]
            ax.plot(x_fit, y_fit, "r--", label="Ajuste lineal")
            ax.legend()
            ax.grid(True)
        elif n_dim == 2:
            sc = ax.scatter(
                positions_km[:, 0],
                positions_km[:, 1],
                c=delays,
                s=100,
                cmap="viridis",
            )
            ax.set_xlabel("X (km)")
            ax.set_ylabel("Y (km)")
            ax.set_title("Delays en el plano XY")
            plt.colorbar(sc, ax=ax, label="Delay (días)")
            # Dibujar vector de dirección
            scale = 0.1 * np.max(np.abs(positions_km))
            dir_vec = result["direction_vector"]
            ax.arrow(
                0,
                0,
                dir_vec[0] * scale,
                dir_vec[1] * scale,
                head_width=0.05 * scale,
                head_length=0.1 * scale,
                fc="r",
                ec="r",
                label="Dirección",
            )
            ax.legend()
            ax.grid(True)
            ax.axis("equal")

        # Gráfico 2: Histograma de velocidades aparentes entre pares (solo para 1D)
        ax = axes[1]
        if n_dim == 1 and "pairwise_velocities" in result:
            pairwise_vel = result["pairwise_velocities"]
            ax.hist(pairwise_vel, bins="auto", edgecolor="black")
            ax.axvline(
                result["velocity_km_per_day"],
                color="r",
                linestyle="--",
                label=f'Velocidad ajustada: {result["velocity_km_per_day"]:.2f} km/día',
            )
            ax.set_xlabel("Velocidad (km/día)")
            ax.set_ylabel("Frecuencia")
            ax.set_title("Velocidades entre pares consecutivos")
            ax.legend()
            ax.grid(True)
        else:
            ax.text(
                0.5, 0.5, "No disponible para 2D/3D", ha="center", va="center"
            )
            ax.set_title("Velocidades entre pares")

        # Gráfico 3: Resumen numérico
        ax = axes[2]
        ax.axis("off")

        # Crear texto de resumen
        summary_lines = [
            "RESUMEN DE PROPAGACIÓN",
            "======================",
            f"Número de sensores: {len(delays)}",
            f"R² del ajuste: {result['R2']:.4f}",
            "",
            "VELOCIDADES:",
            f"  {result['velocity_km_per_day']:.2f} km/día",
            f"  {result['velocity_km_per_hour']:.2f} km/hora",
            f"  {result['velocity_m_per_s']:.2f} m/s",
        ]

        if n_dim == 1:
            summary_lines.extend(
                [
                    "",
                    "INTERCEPTO:",
                    f"  {result['intercept_km']:.2f} km",
                ]
            )
        else:
            summary_lines.extend(
                [
                    "",
                    "DIRECCIÓN (vector unitario):",
                    f"  [{result['direction_vector'][0]:.3f}, {result['direction_vector'][1]:.3f}]",
                ]
            )
            if n_dim == 2:
                summary_lines.extend(
                    [
                        f"  Ángulo: {result['angle_deg']:.1f}°",
                    ]
                )

        summary_text = "\n".join(summary_lines)

        ax.text(
            0.1,
            0.95,
            summary_text,
            transform=ax.transAxes,
            fontfamily="monospace",
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

        plt.tight_layout()
        return fig, axes, result


if __name__ == "__main__":
    # Ejecutar pruebas
    test_lang_selection()

    # Mostrar idioma detectado actualmente
    print(f"Idioma detectado actualmente: {_get_lang(None)}")



!pip install colorama
from typing import Union, Optional
from enum import Enum
from dataclasses import dataclass
import textwrap
from colorama import init, Fore, Style

# Inicializar colorama para colores en consola
init(autoreset=True)

# ============================================================================
# CONFIGURACIÓN DE VALORES VÁLIDOS
# ============================================================================

class DatasetType(Enum):
    """Tipos de datasets disponibles"""
    LANDSAT = "landsat"
    SENTINEL = "sentinel"

class SceneType(Enum):
    """Tipos de escenas disponibles"""
    URBAN = "urban"
    RURAL = "rural"
    COASTAL = "coastal"
    FOREST = "forest"

class OriginType(Enum):
    """Orígenes de datos disponibles"""
    NASA = "nasa"
    ESA = "esa"
    USGS = "usgs"
    JAXA = "jaxa"

class VersionType(Enum):
    """Versiones disponibles"""
    V1_0 = "v1.0"
    V2_0 = "v2.0"
    V2_1 = "v2.1"
    V3_0 = "v3.0"

# Mapeo de datasets a escenas permitidas
DATASET_SCENES = {
    DatasetType.LANDSAT: [SceneType.URBAN, SceneType.RURAL, SceneType.FOREST],
    DatasetType.SENTINEL: [SceneType.URBAN, SceneType.COASTAL, SceneType.FOREST],
}

# Mapeo de datasets a orígenes permitidos
DATASET_ORIGINS = {
    DatasetType.LANDSAT: [OriginType.NASA, OriginType.USGS],
    DatasetType.SENTINEL: [OriginType.ESA],
}

# ============================================================================
# CLASES BASE
# ============================================================================

@dataclass
class GridsatBase:
    """Clase base para datasets Gridsat"""
    dataset: DatasetType
    scene: SceneType
    origins: list[OriginType]
    versions: list[VersionType]

    def __post_init__(self):
        """Validación después de la inicialización"""
        self._validate()

    def _validate(self):
        """Método de validación común"""
        if self.dataset not in DATASET_SCENES:
            raise ValueError(f"Dataset {self.dataset} no válido")

        if self.scene not in DATASET_SCENES[self.dataset]:
            raise ValueError(
                f"Escena {self.scene} no válida para dataset {self.dataset}. "
                f"Escenas permitidas: {[s.value for s in DATASET_SCENES[self.dataset]]}"
            )

        for origin in self.origins:
            if origin not in DATASET_ORIGINS[self.dataset]:
                raise ValueError(
                    f"Origen {origin} no válido para dataset {self.dataset}. "
                    f"Orígenes permitidos: {[o.value for o in DATASET_ORIGINS[self.dataset]]}"
                )

    def process(self):
        """Método para procesar datos"""
        raise NotImplementedError

class LandsatGridsat(GridsatBase):
    """Clase específica para dataset Landsat"""

    def __init__(self, scene: SceneType, origins: list[OriginType], versions: list[VersionType]):
        super().__init__(
            dataset=DatasetType.LANDSAT,
            scene=scene,
            origins=origins,
            versions=versions
        )

    def process(self):
        """Procesamiento específico de Landsat"""
        return f"Procesando Landsat - Escena: {self.scene.value}"

    def __str__(self):
        return f"LandsatGridsat(scene={self.scene.value}, origins={[o.value for o in self.origins]})"

class SentinelGridsat(GridsatBase):
    """Clase específica para dataset Sentinel"""

    def __init__(self, scene: SceneType, origins: list[OriginType], versions: list[VersionType]):
        super().__init__(
            dataset=DatasetType.SENTINEL,
            scene=scene,
            origins=origins,
            versions=versions
        )

    def process(self):
        """Procesamiento específico de Sentinel"""
        return f"Procesando Sentinel - Escena: {self.scene.value}"

    def __str__(self):
        return f"SentinelGridsat(scene={self.scene.value}, origins={[o.value for o in self.origins]})"

# ============================================================================
# FUNCIÓN FACTORÍA CON AYUDA ELEGANTE
# ============================================================================

def print_help(
    missing_param: Optional[str] = None,
    dataset: Optional[str] = None,
    scene: Optional[str] = None
) -> None:
    """
    Imprime una ayuda estructurada y elegante para el usuario.

    Args:
        missing_param: Parámetro que falta (opcional)
        dataset: Dataset proporcionado (opcional)
        scene: Escena proporcionada (opcional)
    """
    help_text = f"""
{Fore.CYAN}{Style.BRIGHT}{'='*60}
{'GRIDSAT FACTORY - AYUDA'.center(60)}
{'='*60}{Style.RESET_ALL}

{Fore.YELLOW}📋 {Style.BRIGHT}USO:{Style.RESET_ALL}
    use_gridsat(
        dataset='landsat' | 'sentinel',
        scene='urban' | 'rural' | 'coastal' | 'forest',
        origins='nasa' | 'esa' | 'usgs' | 'jaxa' (o lista),
        versions='v1.0' | 'v2.0' | 'v2.1' | 'v3.0' (o lista)
    )

{Fore.RED if missing_param else Fore.YELLOW}⚠️  {Style.BRIGHT}PARÁMETRO REQUERIDO FALTANTE:{Style.RESET_ALL} {missing_param or 'Ninguno'}
"""

    # Información específica basada en lo que ya se proporcionó
    if dataset:
        help_text += f"\n{Fore.GREEN}✅ Dataset proporcionado: {dataset}{Style.RESET_ALL}\n"

    if scene:
        help_text += f"{Fore.GREEN}✅ Escena proporcionada: {scene}{Style.RESET_ALL}\n"

    help_text += f"""
{Fore.GREEN}📊 {Style.Bright}DATASETS DISPONIBLES:{Style.RESET_ALL}
    {Fore.CYAN}• landsat{Style.RESET_ALL}
      - Escenas: {', '.join([s.value for s in DATASET_SCENES[DatasetType.LANDSAT]])}
      - Orígenes: {', '.join([o.value for o in DATASET_ORIGINS[DatasetType.LANDSAT]])}

    {Fore.CYAN}• sentinel{Style.RESET_ALL}
      - Escenas: {', '.join([s.value for s in DATASET_SCENES[DatasetType.SENTINEL]])}
      - Orígenes: {', '.join([o.value for o in DATASET_ORIGINS[DatasetType.SENTINEL]])}

{Fore.MAGENTA}🎯 {Style.Bright}ESCENAS DISPONIBLES:{Style.RESET_ALL}
"""
    for scene_enum in SceneType:
        datasets_compatibles = [
            d.value for d in DATASET_SCENES
            if scene_enum in DATASET_SCENES[d]
        ]
        help_text += f"    • {scene_enum.value}: compatible con {', '.join(datasets_compatibles)}\n"

    help_text += f"""
{Fore.BLUE}🌍 {Style.Bright}ORÍGENES DISPONIBLES:{Style.RESET_ALL}
"""
    for origin in OriginType:
        help_text += f"    • {origin.value}\n"

    help_text += f"""
{Fore.YELLOW}🔄 {Style.Bright}VERSIONES DISPONIBLES:{Style.RESET_ALL}
"""
    for version in VersionType:
        help_text += f"    • {version.value}\n"

    help_text += f"""
{Fore.CYAN}{'='*60}
{'EJEMPLOS:'.center(60)}
{'='*60}{Style.RESET_ALL}

{Fore.WHITE}Ejemplo 1:{Style.RESET_ALL}
    use_gridsat(
        dataset='landsat',
        scene='urban',
        origins='nasa',
        versions='v2.0'
    )

{Fore.WHITE}Ejemplo 2:{Style.RESET_ALL}
    use_gridsat(
        dataset='sentinel',
        scene='coastal',
        origins=['esa'],
        versions=['v2.1', 'v3.0']
    )

{Fore.CYAN}{'='*60}{Style.RESET_ALL}
"""

    # Usar textwrap para mantener el formato limpio
    print(textwrap.dedent(help_text))

def use_gridsat(
    *,  # Hacemos todos los parámetros keyword-only
    dataset: Optional[str] = None,
    scene: Optional[str] = None,
    origins: Optional[Union[str, list[str]]] = None,
    versions: Optional[Union[str, list[str]]] = None
) -> Union[LandsatGridsat, SentinelGridsat]:
    """
    Función factoría para crear instancias de Gridsat.

    Args:
        dataset: Tipo de dataset ('landsat' o 'sentinel')
        scene: Tipo de escena ('urban', 'rural', 'coastal', 'forest')
        origins: Origen(es) de los datos (string o lista)
        versions: Versión(es) de los datos (string o lista)

    Returns:
        Instancia de LandsatGridsat o SentinelGridsat

    Raises:
        ValueError: Si los parámetros no son válidos
    """
    # ========================================================================
    # VALIDACIÓN DE PARÁMETROS REQUERIDOS
    # ========================================================================
    missing_params = []

    if dataset is None:
        missing_params.append("dataset")
    if scene is None:
        missing_params.append("scene")

    if missing_params:
        print_help(missing_param=", ".join(missing_params))
        raise ValueError(f"Parámetros requeridos faltantes: {', '.join(missing_params)}")

    # ========================================================================
    # VALIDACIÓN Y CONVERSIÓN DE PARÁMETROS
    # ========================================================================
    try:
        # Convertir string a Enum
        dataset_enum = DatasetType(dataset.lower())
        scene_enum = SceneType(scene.lower())
    except ValueError as e:
        print_help(dataset=dataset, scene=scene)
        raise ValueError(f"Parámetro no válido: {e}")

    # Procesar origins (convertir a lista si es string)
    if origins is None:
        origins_list = []
    elif isinstance(origins, str):
        origins_list = [origins.lower()]
    else:
        origins_list = [o.lower() for o in origins]

    # Convertir origins a Enum
    origins_enums = []
    for origin in origins_list:
        try:
            origins_enums.append(OriginType(origin))
        except ValueError:
            print_help(dataset=dataset, scene=scene)
            raise ValueError(f"Origen no válido: {origin}")

    # Procesar versions (convertir a lista si es string)
    if versions is None:
        versions_list = []
    elif isinstance(versions, str):
        versions_list = [versions.lower()]
    else:
        versions_list = [v.lower() for v in versions]

    # Convertir versions a Enum
    versions_enums = []
    for version in versions_list:
        try:
            versions_enums.append(VersionType(version))
        except ValueError:
            print_help(dataset=dataset, scene=scene)
            raise ValueError(f"Versión no válida: {version}")

    # ========================================================================
    # CREACIÓN DE LA INSTANCIA APROPIADA
    # ========================================================================
    try:
        if dataset_enum == DatasetType.LANDSAT:
            return LandsatGridsat(
                scene=scene_enum,
                origins=origins_enums,
                versions=versions_enums
            )
        elif dataset_enum == DatasetType.SENTINEL:
            return SentinelGridsat(
                scene=scene_enum,
                origins=origins_enums,
                versions=versions_enums
            )
        else:
            raise ValueError(f"Dataset no soportado: {dataset}")

    except ValueError as e:
        print_help(dataset=dataset, scene=scene)
        raise

# ============================================================================
# EJEMPLOS DE USO
# ============================================================================

if __name__ == "__main__":
    # Ejemplo 1: Uso correcto
    print("Ejemplo 1: Uso correcto")
    print("-" * 40)
    try:
        landsat_instance = use_gridsat(
            dataset="landsat",
            scene="urban",
            origins="nasa",
            versions="v2.0"
        )
        print(f"✅ Instancia creada: {landsat_instance}")
        print(f"   Procesamiento: {landsat_instance.process()}")
    except ValueError as e:
        print(f"❌ Error: {e}")

    print("\n" + "="*60 + "\n")

    # Ejemplo 2: Uso con lista de orígenes y versiones
    print("Ejemplo 2: Uso con múltiples orígenes y versiones")
    print("-" * 40)
    try:
        sentinel_instance = use_gridsat(
            dataset="sentinel",
            scene="coastal",
            origins=["esa"],
            versions=["v2.1", "v3.0"]
        )
        print(f"✅ Instancia creada: {sentinel_instance}")
        print(f"   Procesamiento: {sentinel_instance.process()}")
    except ValueError as e:
        print(f"❌ Error: {e}")

    print("\n" + "="*60 + "\n")

    # Ejemplo 3: Falta parámetro requerido (se mostrará ayuda)
    print("Ejemplo 3: Falta parámetro 'scene'")
    print("-" * 40)
    try:
        instance = use_gridsat(
            dataset="landsat",
            origins="nasa",
            versions="v2.0"
        )
    except ValueError as e:
        print(f"❌ Error capturado: {e}")

    print("\n" + "="*60 + "\n")

    # Ejemplo 4: Parámetro inválido (se mostrará ayuda)
    print("Ejemplo 4: Escena inválida para el dataset")
    print("-" * 40)
    try:
        instance = use_gridsat(
            dataset="landsat",
            scene="coastal",  # coastal no está disponible para landsat
            origins="nasa"
        )
    except ValueError as e:
        print(f"❌ Error capturado: {e}")


