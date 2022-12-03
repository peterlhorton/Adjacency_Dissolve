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
    
    return subadjacencies_faster_3([set(i) for i in test_intersection_tuples]) + list(ser[ser==1].index)

def subadjacencies_faster_3(dup_list):
    all_intersections = starmap(set.intersection, combinations(dup_list, 2))
    finished = True
    for val in all_intersections:
        if val != set():
            finished = False
    if finished:
        return [sorted(list(i)) for i in dup_list]
    else:
        final_holder = []
        for val in dup_list:
            added = False
            added_indices = []
            for idx, x in enumerate(final_holder):
                if len(x.intersection(val)) > 0:
                    final_holder[idx] = x.union(val)
                    added_indices.append(idx)
                    added = True
            if len(added_indices) > 1:
                for i in range(1, len(added_indices)):
                    final_holder[added_indices[0]] = final_holder[added_indices[0]].union(final_holder[added_indices[i]])
                for i in range(len(added_indices)-1,0,-1):
                    final_holder.pop(added_indices[i])
            if not added:
                final_holder.append(val)
        return final_holder