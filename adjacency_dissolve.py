import geopandas as gp
from itertools import combinations, starmap

def adjacency_dissolve(gdf, include_point_adjacency = True):
    '''
    Code that takes in a geodataframe and returns the geodataframe with adjacencies dissolved
    Includes a "include_point_adjacency" parameter, with a default value set to "True"
    Currently the code is not fine-tuned to handle non-geometric data during the dissolve 
    '''
    # Make sure that the index column is unique
    if "index" in gdf.columns:
        raise ValueError("Column already named 'index'")
        
    gdf.reset_index(inplace = True, drop = False)
    
    if not gdf.index.is_unique:
        raise ValueError ("Non-unique index column")
    
    adj_groups = calculate_adjacency(gdf, include_point_adjacency)
    
    if "Dissolve_Assignment" in gdf.columns:
        raise ValueError("Existing 'Dissolve_Assignment' column")
    
    gdf["Dissolve_Assignment"] = ""
    for i in range(0,len(adj_groups)):
        if type(adj_groups[i])==gdf.dtypes["index"]:
            gdf.loc[gdf["index"]== adj_groups[i],"Dissolve_Assignment"] = i
        elif type(adj_groups[i])==set:
            gdf.loc[gdf["index"].isin(adj_groups[i]) ,"Dissolve_Assignment"] = i
    
    dissolved = gdf.dissolve("Dissolve_Assignment")
    dissolved.reset_index(drop = False, inplace = True)
    dissolved.drop(["index","Dissolve_Assignment"], axis = 1, inplace = True)
    
    return dissolved


def calculate_adjacency(gdf, include_point_adjacency = True):
    '''
    Code that takes a geodataframe and returns a dictionary of adjacencies

    Includes an 'include_point_adjacency' parameter, default value of True, that can be changed to exclude point adjacencies
    '''    
    # Intersected the GeoDataFrame with the buffer with the original GeoDataFrame
    test_intersection = gp.overlay(gdf, gdf, how = "intersection", keep_geom_type = False)
    
    # If the include_point_adjacency is False
    if (include_point_adjacency == False):
        # Filter out the intersections that are just points
        test_intersection = test_intersection[test_intersection.geom_type != "Point"]
    
    # Get value counts after the intersections
    ser = test_intersection["index_1"].value_counts()
    
    # Filter out self-intersections
    test_intersection = test_intersection[test_intersection["index_1"]!=test_intersection["index_2"]]
    
    # Define a tuple of zips of the unique_col pairs present in the intersection
    test_intersection_tuples = list(list(zip(test_intersection["index_1"], test_intersection["index_2"])))
    
    return merge_adjacencies([set(i) for i in test_intersection_tuples]) + list(ser[ser==1].index)

def merge_adjacencies(list_of_sets):
    '''
    Takes a list of sets and returns a list of lists where the sets have been combined into sorted lists if two sets contain any of the same elements

    Ex. [(9,1), (1,5), (3,6)] -> [[1,5,9], [3,6]]
    '''

    # Perform an intersection across all combinations of two sets
    all_intersections = starmap(set.intersection, combinations(list_of_sets, 2))
    finished = True

    # Iterate over all of the intersections
    for val in all_intersections:
        # If there are any intersections across two of the sets, we will need to do combining
        if val != set():
            finished = False
    # If there are not, we can return the list of sets as a list of sorted lists
    if finished:
        return list_of_sets

    # Otherwise we must combine the values
    else:
        # Define a list to hold the our return value
        final_holder = []
        # Iterate over the list of sets
        for val in list_of_sets:
            added = False
            # Define a list to keep track of indices where the 'val' has a non-empty intersection with the values in final_holder
            added_indices = []
            # Iterate over the final_holder list defined above
            for idx, x in enumerate(final_holder):
                # If there is a non-zero intersection, union the values, and add the indices to the added_indices list
                if len(x.intersection(val)) > 0:
                    final_holder[idx] = x.union(val)
                    added_indices.append(idx)
                    added = True
            # When the val intersects with two of the final_holder elements, those must be combined
            if len(added_indices) > 1:
                for i in range(1, len(added_indices)):
                    final_holder[added_indices[0]] = final_holder[added_indices[0]].union(final_holder[added_indices[i]])
                for i in range(len(added_indices)-1,0,-1):
                    final_holder.pop(added_indices[i])
            # If val does not intersect with any element, append it to final_holder
            if not added:
                final_holder.append(val)
        return final_holder