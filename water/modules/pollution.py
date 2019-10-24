import pandas as pd


def pollution_series(pollution_scenario, timestep):
    """
    Produce a pandas series of the pollution for each node for a given
    injection site and timestep.

    If the timestep has no pollution data a series of zeroes is returned.

    Args:
        pollution_scenario (pandas.Dataframe): A dataframe of the pollution
            values at each node for set of timesteps. The columns of the
            Dataframe are the node labels and the index is a set of timesteps.
        timestep (int): The time step.

    Returns:
        pandas.Series: The pollution value at each node for the given timestep
            and injection location.
    """
    # Extract the pollution series at the given timestep
    if timestep in pollution_scenario.index:
        series = pollution_scenario.loc[timestep]
    else:
        # Construct a series of zero pollution
        size = pollution_scenario.index.size
        series = pd.Series(dict(zip(pollution_scenario.columns,
                                    [0]*size)))

    return series


def pollution_history(pollution_scenario, node):
    """
    Produce a pandas series of the pollution over time for a particular node
    extracted from a pollution scenario.

    Args:
        pollution_scenario (pandas.Dataframe): A dataframe of the pollution
            values at each node for set of timesteps. The columns of the
            Dataframe are the node labels and the index is a set of timesteps.
        node (str): The label of the node.

    Returns:
        pandas.Series: The pollution value at each timestep for the given node
            in the pollution scenario.
    """

    if node is not None:
        return pollution_scenario[node]
    else:
        return pd.Series([])


def pollution_scenario(pollution, injection):
    """
    Produce a pandas dataframe given the pollution in each node over a series
    of timesteps for a given injection site.

    Args:
        pollution (dict): A dictionary of the pollution dynamics as produced by
            wntr. The keys are injection sites and the values are a Pandas
            Dataframe describing the pollution dynamics.  The columns of the
            Dataframe are the node labels and the index is a set of timesteps.
        injection (str): The node label of the injection site.

    Returns:
        pandas.Dataframe: The pollution value at each node for a set of
            timessteps. The columns of the dataframe are the node labels and
            the index is a set of timesteps.
    """
    return pollution[injection]
