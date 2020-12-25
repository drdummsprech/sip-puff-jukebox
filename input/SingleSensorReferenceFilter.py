class SingleSensorReferenceFilter:
    """
    Filter that tries to detect ambient pressure from a sensor that's also used for sipping and puffing.

    The original idea was to use a differential setup with two sensors, but since the BMP280's accuracy is way
    worse than its precision, this was thrown out.
    The basic problem is that the ambient pressure needs to be tracked, since its changes due to weather and location
    are too high to ignore.

    This filter tries to work around the problem by almost ignoring high differentials between the expected ambient
    pressure and the measured pressure. It doesn't entirely ignore them to make sure that even in case of a
    misinitialization it eventually converges to the right value within minutes. As a result sipping and puffing isn't
    filtered out completely, but affects the ambient pressure estimation by an amount that can be practically ignored.

    Attributes:
        expectedVariance    The expected variance of the pressure readings in Pascal
                            This determines the size of the window around the current estimation within which readings
                            are treated as gospel and fully used to update the estimation. Past this window, the
                            influence of a value on the estimation decreases pretty steeply.
    """

    expectedVariance: int = 100

    __cur_observation_count: int = 0
    __observation_count_limit: int = 2_000
    __current_estimation: float = 97_500.0

    def initialize(self, reading):
        self.__current_estimation = reading
        self.__cur_observation_count += 100

    def update(self, reading: float):
        """
        Updates the estimation by processing the given pressure measurement
        :param reading: The pressure reading in Pascal
        :return: None. As a side effect the current estimation for the ambient pressure might change
        """

        if self.__cur_observation_count < 10:
            self.initialize(reading)

        diff = self.__current_estimation - reading
        attenuation_factor = abs(diff / self.expectedVariance)
        if attenuation_factor == 0:
            return
        weight = 1.0 / attenuation_factor
        weight = min(10.0, weight)
        # weight = max(0.02, weight)

        # We are weighting the current observation based on how much it diverges
        # from our expectation.
        # This is sensitive to slow changes and basically suppresses large
        # differences such as when sipping or puffing
        a = self.__current_estimation * self.__cur_observation_count
        b = reading * weight
        c = self.__cur_observation_count + weight

        self.__current_estimation = (a + b) / c

        self.__cur_observation_count += 1
        self.__cur_observation_count = min(self.__observation_count_limit, self.__cur_observation_count)

    def get_ambient_pressure_estimation(self) -> float:
        """This should only called after at least one call to update with an actual sensor reading"""
        return self.__current_estimation
