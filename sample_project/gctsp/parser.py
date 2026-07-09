import os
import numpy as np

def parse_gctsp(filepath):
    """
    Parses a .gctsp file and returns a dictionary of its parsed elements and computed distance matrix.
    """
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f.readlines()]
        
    header = {}
    coords = []
    covering_sets = []
    mode = 'HEADER'
    
    for line in lines:
        if not line:
            if mode == 'COVERING_SETS':
                covering_sets.append(set())
            continue
        if line == 'EOF':
            break
            
        if mode == 'HEADER':
            if line.startswith('NODE_COORD_SECTION'):
                mode = 'COORDS'
                continue
            parts = line.split(':')
            if len(parts) == 2:
                header[parts[0].strip()] = parts[1].strip()
        elif mode == 'COORDS':
            if line.startswith('COVERING_SETS'):
                mode = 'COVERING_SETS'
                continue
            parts = line.split()
            coords.append((float(parts[1]), float(parts[2])))
        elif mode == 'COVERING_SETS':
            parts = {int(x) for x in line.split()}
            covering_sets.append(parts)
            
    name = header.get('NAME', 'GCTSP')
    num_nodes = int(header.get('NODES', 0))
    depot = int(header.get('DEPOT', 0))
    num_customers = int(header.get('CUSTOMERS', 0))
    quota = int(header.get('QUOTA', 0))
    edge_weight_type = header.get('EDGE_WEIGHT_TYPE', 'EUC_2D')
    
    # Identify unique facility indices mentioned in covering sets
    facility_nodes = sorted(list({fac for cs in covering_sets for fac in cs}))
    
    # Customer nodes are the remaining nodes (excluding depot 0 and facility nodes)
    all_nodes = set(range(1, num_nodes))
    customer_nodes = sorted(list(all_nodes - set(facility_nodes)))
    
    # Calculate distance matrix
    distances = np.zeros((num_nodes, num_nodes), dtype=np.float64)
    
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i == j:
                distances[i, j] = 0.0
                continue
                
            c1 = coords[i]
            c2 = coords[j]
            
            if edge_weight_type == 'EUC_2D':
                dx = c1[0] - c2[0]
                dy = c1[1] - c2[1]
                distances[i, j] = np.sqrt(dx*dx + dy*dy)
                
            elif edge_weight_type == 'GEO':
                PI = 3.141592
                def to_rad(coord):
                    deg = int(coord)
                    min_part = coord - deg
                    return PI * (deg + 5.0 * min_part / 3.0) / 180.0
                
                lat1, lon1 = to_rad(c1[0]), to_rad(c1[1])
                lat2, lon2 = to_rad(c2[0]), to_rad(c2[1])
                
                RRR = 6378.388
                q1 = np.cos(lon1 - lon2)
                q2 = np.cos(lat1 - lat2)
                q3 = np.cos(lat1 + lat2)
                
                distances[i, j] = int(RRR * np.arccos(0.5 * ((1.0 + q1) * q2 - (1.0 - q1) * q3)) + 1.0)
                
            elif edge_weight_type == 'ATT':
                xd = c1[0] - c2[0]
                yd = c1[1] - c2[1]
                rij = np.sqrt((xd*xd + yd*yd) / 10.0)
                t = int(np.round(rij))
                distances[i, j] = t + 1 if t < rij else t
                
            else:
                # Default to Euclidean
                dx = c1[0] - c2[0]
                dy = c1[1] - c2[1]
                distances[i, j] = np.sqrt(dx*dx + dy*dy)
                
    return {
        'name': name,
        'num_nodes': num_nodes,
        'depot': depot,
        'num_customers': num_customers,
        'quota': quota,
        'edge_weight_type': edge_weight_type,
        'coords': coords,
        'covering_sets': covering_sets,
        'facility_nodes': facility_nodes,
        'customer_nodes': customer_nodes,
        'distances': distances
    }
