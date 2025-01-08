import pytest

from darts.utils.model_selection import MODEL_AWARE, SIMPLE, train_test_split
from darts.utils.timeseries_generation import constant_timeseries


def make_dataset(rows, cols):
    return [constant_timeseries(value=i, length=cols) for i in range(rows)]


def verify_shape(dataset, rows, cols):
    return len(dataset) == rows and all(len(row) == cols for row in dataset)


class TestClassTrainTestSplit:
    def test_parameters_for_axis_0(self):
        # expecting no exception
        train_test_split(make_dataset(2, 10), axis=0, test_size=1)

    def test_parameters_for_axis_1_no_n(self):
        with pytest.raises(AttributeError) as err:
            train_test_split(
                make_dataset(1, 10), axis=1, horizon=1, vertical_split_type=MODEL_AWARE
            )
        assert (
            str(err.value)
            == "You need to provide non-zero `horizon` and `input_size` parameters when axis=1"
        )

    def test_parameters_for_axis_1_no_horizon(self):
        with pytest.raises(AttributeError) as err:
            train_test_split(
                make_dataset(1, 10),
                axis=1,
                input_size=1,
                vertical_split_type=MODEL_AWARE,
            )
        assert (
            str(err.value)
            == "You need to provide non-zero `horizon` and `input_size` parameters when axis=1"
        )

    def test_empty_dataset(self):
        with pytest.raises(AttributeError):
            train_test_split([])

    def test_horiz_number_of_samples_too_small(self):
        with pytest.raises(AttributeError) as err:
            train_set, test_set = train_test_split(
                make_dataset(1, 10),
                axis=1,
                input_size=4,
                horizon=7,
                test_size=1,
                vertical_split_type=MODEL_AWARE,
            )
        assert str(err.value) == "Not enough data to create training and test sets"

    def test_sunny_day_horiz_split(self):
        train_set, test_set = train_test_split(make_dataset(8, 10))

        assert verify_shape(train_set, 6, 10) and verify_shape(test_set, 2, 10), (
            f"Wrong shapes: training set shape: ({len(train_set)}, {len(train_set[0])});"
            f" test set shape ({len(test_set)}, {len(test_set[0])})"
        )

    def test_sunny_day_horiz_split_absolute(self):
        train_set, test_set = train_test_split(make_dataset(8, 10), test_size=2)

        assert verify_shape(train_set, 6, 10) and verify_shape(test_set, 2, 10), (
            f"Wrong shapes: training set shape: ({len(train_set)}, {len(train_set[0])});"
            f" test set shape ({len(test_set)}, {len(test_set[0])})"
        )

    def test_horiz_split_overindexing_train_set(self):
        train_set, test_set = train_test_split(make_dataset(8, 10), lazy=True)
        with pytest.raises(IndexError) as err:
            train_set[6]
        assert str(err.value) == "Exceeded the size of the training sequence."

    def test_horiz_split_last_index_train_set(self):
        train_set, test_set = train_test_split(make_dataset(8, 10), lazy=True)
        # no IndexError is thrown
        train_set[5]

    def test_horiz_split_overindexing_test_set(self):
        train_set, test_set = train_test_split(make_dataset(8, 10), lazy=True)

        with pytest.raises(IndexError) as err:
            test_set[2]
        assert str(err.value) == "Exceeded the size of the test sequence."

    def test_horiz_split_last_index_test_set(self):
        train_set, test_set = train_test_split(make_dataset(8, 10))
        # no IndexError is thrown

    # test 6
    def test_sunny_day_vertical_split(self):
        train_set, test_set = train_test_split(
            make_dataset(2, 250),
            axis=1,
            input_size=70,
            horizon=50,
            vertical_split_type=MODEL_AWARE,
        )

        assert verify_shape(train_set, 2, 151) and verify_shape(test_set, 2, 169), (
            f"Wrong shapes: training set shape: ({len(train_set)}, {len(train_set[0])});"
            f" test set shape ({len(test_set)}, {len(test_set[0])})"
        )

    # test 7
    def test_test_split_absolute_number_horiz(self):
        train_set, test_set = train_test_split(make_dataset(4, 10), axis=0, test_size=2)

        assert verify_shape(train_set, 2, 10) and verify_shape(test_set, 2, 10)

    # test 8
    def test_test_split_absolute_number_vertical(self):
        train_set, test_set = train_test_split(
            make_dataset(4, 10),
            axis=1,
            test_size=2,
            input_size=1,
            horizon=2,
            vertical_split_type=MODEL_AWARE,
        )

        assert verify_shape(train_set, 4, 7) and verify_shape(test_set, 4, 4), (
            f"Wrong shapes: training set shape: ({len(train_set)}, {len(train_set[0])});"
            f" test set shape ({len(test_set)}, {len(test_set[0])})"
        )

    def test_negative_test_start_index(self):
        with pytest.raises(AttributeError) as err:
            train_set, test_set = train_test_split(
                make_dataset(1, 10),
                axis=1,
                input_size=2,
                horizon=9,
                test_size=1,
                vertical_split_type=MODEL_AWARE,
            )
        assert str(err.value) == "Not enough data to create training and test sets"

    def test_horiz_split_horizon_equal_to_ts_length(self):
        with pytest.raises(AttributeError) as err:
            train_set, test_set = train_test_split(
                make_dataset(1, 10),
                axis=1,
                input_size=2,
                horizon=10,
                test_size=1,
                vertical_split_type=MODEL_AWARE,
            )
        assert str(err.value) == "Not enough data to create training and test sets"

    def test_single_timeseries_no_horizon_no_n(self):
        with pytest.raises(AttributeError):
            # even if the default axis is 0, but since it is a single timeseries, default axis is 1
            train_test_split(
                constant_timeseries(value=123, length=10),
                test_size=2,
                vertical_split_type=MODEL_AWARE,
            )

    def test_single_timeseries_sunny_day(self):
        train_set, test_set = train_test_split(
            constant_timeseries(value=123, length=10),
            test_size=2,
            input_size=1,
            horizon=2,
            vertical_split_type=MODEL_AWARE,
        )

        assert len(train_set) == 7 and len(test_set) == 4, (
            f"Wrong shapes: training set shape: {len(train_set)}; test set shape {len(test_set)}"
        )

    def test_multi_timeseries_variable_ts_length_sunny_day(self):
        data = [
            constant_timeseries(value=123, length=10),
            constant_timeseries(value=123, length=100),
            constant_timeseries(value=123, length=1000),
        ]
        train_set, test_set = train_test_split(
            data,
            axis=1,
            test_size=2,
            input_size=1,
            horizon=2,
            vertical_split_type=MODEL_AWARE,
        )
        train_lengths = [len(ts) for ts in train_set]
        test_lengths = [len(ts) for ts in test_set]

        assert train_lengths == [7, 97, 997] and test_lengths == [
            4,
            4,
            4,
        ], (
            f"Wrong shapes: training set shape: {train_lengths}; test set shape {test_lengths}"
        )

    def test_multi_timeseries_variable_ts_length_one_ts_too_small(self):
        data = [
            constant_timeseries(value=123, length=21),
            constant_timeseries(value=123, length=100),
            constant_timeseries(value=123, length=1000),
        ]
        with pytest.raises(AttributeError) as err:
            train_set, test_set = train_test_split(
                data,
                axis=1,
                test_size=2,
                input_size=1,
                horizon=18,
                vertical_split_type=MODEL_AWARE,
            )
        assert str(err.value) == "Not enough data to create training and test sets"

    def test_simple_vertical_split_sunny_day(self):
        train_set, test_set = train_test_split(
            make_dataset(4, 10), axis=1, vertical_split_type=SIMPLE, test_size=0.2
        )

        assert verify_shape(train_set, 4, 8) and verify_shape(test_set, 4, 2), (
            f"Wrong shapes: training set shape: ({len(train_set)}, {len(train_set[0])});"
            f" test set shape ({len(test_set)}, {len(test_set[0])})"
        )

    def test_simple_vertical_split_sunny_day_absolute_split(self):
        train_set, test_set = train_test_split(
            make_dataset(4, 10), axis=1, vertical_split_type=SIMPLE, test_size=2
        )

        assert verify_shape(train_set, 4, 8) and verify_shape(test_set, 4, 2), (
            f"Wrong shapes: training set shape: ({len(train_set)}, {len(train_set[0])});"
            f" test set shape ({len(test_set)}, {len(test_set[0])})"
        )

    def test_simple_vertical_split_exception_on_bad_param(self):
        # bad value for vertical_split_type
        with pytest.raises(AttributeError):
            train_set, test_set = train_test_split(
                make_dataset(4, 10),
                axis=1,
                vertical_split_type="WRONG_VALUE",
                test_size=2,
            )

    def test_simple_vertical_split_test_size_too_large(self):
        with pytest.raises(AttributeError) as err:
            train_set, test_set = train_test_split(
                make_dataset(4, 10), axis=1, vertical_split_type=SIMPLE, test_size=11
            )
        assert str(err.value) == "`test_size` is bigger then timeseries length"

    def test_model_aware_vertical_split_empty_training_set(self):
        with pytest.raises(AttributeError) as err:
            train_set, test_set = train_test_split(
                make_dataset(4, 10),
                axis=1,
                vertical_split_type=MODEL_AWARE,
                test_size=5,
                horizon=3,
                input_size=2,
            )
        assert str(err.value) == "Not enough data to create training and test sets"
