import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from darts import TimeSeries
from darts.dataprocessing.transformers import Scaler
from darts.utils import timeseries_generation as tg
from darts.utils.timeseries_generation import linear_timeseries, sine_timeseries


class TestDataTransformer:
    series1 = tg.random_walk_timeseries(length=100, column_name="series1") * 20 - 10.0
    series2 = series1.stack(tg.random_walk_timeseries(length=100) * 20 - 100.0)

    col_1 = series1.columns

    def test_scaling(self):
        series3 = self.series1[:1]
        input_series_copy = [s.copy() for s in [self.series1, self.series2, series3]]
        transformer1 = Scaler(MinMaxScaler(feature_range=(0, 2)))
        transformer2 = Scaler(StandardScaler())

        series1_tr1 = transformer1.fit_transform(self.series1)
        series1_tr2 = transformer2.fit_transform(self.series1)
        series3_tr2 = transformer2.transform(series3)
        tr_series_copy = [s.copy() for s in [series1_tr1, series1_tr2, series3_tr2]]

        # should have the defined name above
        assert self.series1.columns[0] == "series1"

        # should keep columns pd.Index
        assert self.col_1 == series1_tr1.columns

        # should comply with scaling constraints
        assert round(abs(min(series1_tr1.values().flatten()) - 0.0), 7) == 0
        assert round(abs(max(series1_tr1.values().flatten()) - 2.0), 7) == 0
        assert round(abs(np.mean(series1_tr2.values().flatten()) - 0.0), 7) == 0
        assert round(abs(np.std(series1_tr2.values().flatten()) - 1.0), 7) == 0

        # test inverse transform
        series1_recovered = transformer2.inverse_transform(series1_tr2)
        series3_recovered = transformer2.inverse_transform(series3_tr2)
        np.testing.assert_almost_equal(
            series1_recovered.values().flatten(), self.series1.values().flatten()
        )
        assert series1_recovered.width == self.series1.width
        assert series3_recovered == series1_recovered[:1]

        assert [self.series1, self.series2, series3] == input_series_copy
        assert [series1_tr1, series1_tr2, series3_tr2] == tr_series_copy

    def test_multi_ts_scaling(self):
        transformer1 = Scaler(MinMaxScaler(feature_range=(0, 2)))
        transformer2 = Scaler(StandardScaler())

        series_array = [self.series1, self.series2]

        series_array_tr1 = transformer1.fit_transform(series_array)
        series_array_tr2 = transformer2.fit_transform(series_array)

        for index in range(len(series_array)):
            assert (
                round(abs(min(series_array_tr1[index].values().flatten()) - 0.0), 7)
                == 0
            )
            assert (
                round(abs(max(series_array_tr1[index].values().flatten()) - 2.0), 7)
                == 0
            )
            assert (
                round(abs(np.mean(series_array_tr2[index].values().flatten()) - 0.0), 7)
                == 0
            )
            assert (
                round(abs(np.std(series_array_tr2[index].values().flatten()) - 1.0), 7)
                == 0
            )

        series_array_rec1 = transformer1.inverse_transform(series_array_tr1)
        series_array_rec2 = transformer2.inverse_transform(series_array_tr2)

        for index in range(len(series_array)):
            np.testing.assert_almost_equal(
                series_array_rec1[index].values().flatten(),
                series_array[index].values().flatten(),
            )
            np.testing.assert_almost_equal(
                series_array_rec2[index].values().flatten(),
                series_array[index].values().flatten(),
            )

    def test_multivariate_stochastic_series(self):
        scaler = Scaler(MinMaxScaler())
        vals = np.random.rand(10, 5, 50)
        s = TimeSeries.from_values(vals)
        ss = scaler.fit_transform(s)
        ssi = scaler.inverse_transform(ss)

        # Test inverse transform
        np.testing.assert_allclose(s.all_values(), ssi.all_values())

        # Test that the transform is done per component (i.e max value over each component should be 1 and min 0)
        np.testing.assert_allclose(
            np.array([
                ss.all_values(copy=False)[:, i, :].max() for i in range(ss.width)
            ]),
            np.array([1.0] * ss.width),
        )

        np.testing.assert_allclose(
            np.array([
                ss.all_values(copy=False)[:, i, :].min() for i in range(ss.width)
            ]),
            np.array([0.0] * ss.width),
        )

    def test_component_mask_transformation(self):
        scaler = Scaler(MinMaxScaler())
        # shape = (10, 3, 2)
        vals = np.array([np.arange(6).reshape(3, 2)] * 10)

        # scalers should only consider True columns
        component_mask = np.array([True, False, True])

        s = TimeSeries.from_values(vals)
        ss = scaler.fit_transform(s, component_mask=component_mask)
        ss_vals = ss.all_values(copy=False)

        # test non-masked columns
        assert (ss_vals[:, 1, :] == vals[:, 1, :]).all()
        # test masked columns
        assert round(abs(ss_vals[:, [0, 2], :].max() - 1.0), 7) == 0
        assert round(abs(ss_vals[:, [0, 2], :].min() - 0.0), 7) == 0

        ssi = scaler.inverse_transform(ss, component_mask=component_mask)

        # Test inverse transform
        np.testing.assert_allclose(s.all_values(), ssi.all_values())

    def test_global_fitting(self):
        """
        Tests that `Scaler` correctly handles situation where `global_fit = True`. More
        specifically, test checks that global fitting with two disjoint series
        produces same fitted parameters as local fitting with a single series formed
        by 'gluing' these two disjoint series together.
        """
        sine_series = sine_timeseries(length=50, value_y_offset=5, value_frequency=0.05)
        lin_series = linear_timeseries(start_value=1, end_value=10, length=50)
        series_combined = sine_series.append_values(lin_series.all_values())
        local_fitted_scaler = (
            Scaler(global_fit=False).fit(series_combined)._fitted_params[0]
        )
        global_fitted_scaler = (
            Scaler(global_fit=True).fit([sine_series, lin_series])._fitted_params[0]
        )
        assert local_fitted_scaler.get_params() == global_fitted_scaler.get_params()
