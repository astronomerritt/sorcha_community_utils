from sorcha.activity.base_activity import AbstractCometaryActivity
from .model import Comet
from typing import List
import pandas as pd
import numpy as np


class LSSTCometActivity(AbstractCometaryActivity):
    """
    Calculating the coma magnitude of a comet with input specifications.

    The observation dataframe provided to the ``compute``
    method should have the following columns:

    * ``k`` - Dust falling exponential value (dust falling at rh^k)
    * ``afrho1`` - Quantity of A'Hearn et al. (1984). at perihelion (cm). See notes.
    * ``optFilter`` - Observing filter of the observation
    * ``TrailedSourceMag`` - Apparent magnitude in the input filter of the comet nucleus adding up all of the counts in the trail

    Notes:
    ``afrho1`` - The product of albedo, filling factor of grains within the observer field
    of view, and the linear radius of the field of view at the comet

    This class is derived from ``lsstcomet`` by Mike Kelley (C)  LSST Solar System Scientific Collaboration 2019
    """

    def __init__(
        self, required_column_names: List[str] = ["k", "afrho1", "optFilter", "TrailedSourceMag"]
    ) -> None:
        super().__init__(required_column_names)

    def compute(
        self,
        df: pd.DataFrame,
        observing_filters: List[str],
        rho: List[float],
        delta: List[float],
        alpha: List[float],
    ) -> pd.DataFrame:
        """
        Returns numpy array of 0's with shape equal to the input dataframe
        time column.

        Parameters
        ----------
        df : pd.DataFrame
            The ``observations`` dataframe provided by ``Sorcha``.
        observing_filters : List[str]
            The photometric filters the observation is taken in (the filter
            requested that the coma magnitude be calculated for)
        rho : List[float]
            Heliocentric distance [units au]
        delta : List[float]
            Distance to Earth [units au]
        alpha : List[float]
            Phase angle [units degrees]

        Returns
        -------
        pd.DataFrame
            The original ``observations`` dataframe, with updated magnitude values
            based on results of `lsstcomet` coma calculations.
        """

        self._validate_column_names(df)

        com = Comet(k=df.k, afrho1=df.afrho1)

        # this is the geometrical data
        g = {"rh": rho, "delta": delta, "phase": alpha}

        # this calculates the coma magnitude in each filter
        try:
            for filt in observing_filters:
                df.loc[df["optFilter"] == filt, "coma_magnitude"] = com.mag(g, filt, rap=df["seeingFwhmEff"])
        except KeyError as err:
            self._log_exception(err)

        df["TrailedSourceMag"] = -2.5 * np.log10(
            10 ** (-0.4 * df["coma_magnitude"]) + 10 ** (-0.4 * df["TrailedSourceMag"])
        )

        return df

    @staticmethod
    def name_id() -> str:
        """Returns the string identifier for this cometary activity method. It
        must be unique within all the subclasses of ``AbstractCometaryActivity``.

        Returns
        -------
        str
            Unique identifier for this cometary activity model
        """
        return "lsst_comet"
