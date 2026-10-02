import pandas as pd

def add_user_counts_to_population_density(user_df, pop_df, platform_name='platform'):
    """
    Adds a column to the population density dataframe with the count of users per city.

    Args:
        user_df (pd.DataFrame): DataFrame containing user data with a city column.
        platform_name (str): Name of the platform (used as the new column name).

    Returns:
        pd.DataFrame: The population density dataframe with an added column for user counts.
    """
    # Count users per city
    user_counts = user_df['Gemeindename'].value_counts().rename(platform_name)

    # Merge counts into population density dataframe
    pop_df = pop_df.merge(user_counts, how='left', left_on='City', right_index=True)
    
    # Fill NaN with 0 (no users registered in that city)
    pop_df[platform_name] = pop_df[platform_name].fillna(0).astype(int)

    if 'Is active' in user_df.columns:
        active_user_df = user_df[user_df['Is active']]
        active_user_counts = active_user_df['Gemeindename'].value_counts().rename(platform_name)
        pop_df = pop_df.merge(active_user_counts, how='left', left_on='City', right_index=True, suffixes=('', '_active'))
        pop_df[platform_name + '_active'] = pop_df[platform_name + '_active'].fillna(0).astype(int)
    elif 'Recently active' in user_df.columns:
        active_user_df = user_df[user_df['Recently active']]
        active_user_counts = active_user_df['Gemeindename'].value_counts().rename(platform_name)
        pop_df = pop_df.merge(active_user_counts, how='left', left_on='City', right_index=True, suffixes=('', '_active'))
        pop_df[platform_name + '_active'] = pop_df[platform_name + '_active'].fillna(0).astype(int)
    
    return pop_df

# Example usage:
# user_df = pd.read_csv('path_to_user_data.csv')
# result_df = add_user_counts_to_population_density(user_df, 'plz_data/population_density.csv', user_city_col='city', platform_name='my_platform')
# result_df.to_csv('plz_data/population_density_with_users.csv', index=False)