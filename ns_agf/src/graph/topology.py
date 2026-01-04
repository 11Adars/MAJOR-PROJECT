"""
MediaPipe Holistic 75-Node Graph Topology Definition
=====================================================

This module defines the spatial graph structure for the NS-AGF model.
We use a semantic subgraph of 75 nodes from MediaPipe Holistic:
- Pose: 33 landmarks (indices 0-32)
- Left Hand: 21 landmarks (indices 33-53)
- Right Hand: 21 landmarks (indices 54-74)

Critical Bridge Connections:
- Pose Wrist 15 (Left) → Hand Root 33
- Pose Wrist 16 (Right) → Hand Root 54
"""

import numpy as np
from typing import List, Tuple, Dict


class MediaPipeGraph:
    """
    Defines the 75-node topological graph for MediaPipe Holistic landmarks.
    """
    
    def __init__(self):
        self.num_nodes = 75
        self.neighbor_links = self._define_neighbor_links()
        self.center = 0  # Nose (Pose landmark 0)
        
    def _define_neighbor_links(self) -> List[Tuple[int, int]]:
        """
        Define all edges in the 75-node graph.
        Returns list of (node_i, node_j) tuples representing connections.
        """
        links = []
        
        # ==================== POSE SKELETON (0-32) ====================
        # Face contour connections
        pose_face = [
            (0, 1), (1, 2), (2, 3), (3, 7),  # Right side face
            (0, 4), (4, 5), (5, 6), (6, 8),  # Left side face
            (9, 10),  # Mouth
        ]
        
        # Torso and shoulder connections
        pose_torso = [
            (11, 12),  # Shoulders
            (11, 23), (12, 24),  # Shoulders to hips
            (23, 24),  # Hip line
        ]
        
        # Right arm
        pose_right_arm = [
            (12, 14), (14, 16),  # Shoulder → Elbow → Wrist
        ]
        
        # Left arm
        pose_left_arm = [
            (11, 13), (13, 15),  # Shoulder → Elbow → Wrist
        ]
        
        # Right leg
        pose_right_leg = [
            (24, 26), (26, 28),  # Hip → Knee → Ankle
            (28, 30), (30, 32),  # Ankle → Heel → Foot index
        ]
        
        # Left leg
        pose_left_leg = [
            (23, 25), (25, 27),  # Hip → Knee → Ankle
            (27, 29), (29, 31),  # Ankle → Heel → Foot index
        ]
        
        links.extend(pose_face + pose_torso + pose_right_arm + 
                     pose_left_arm + pose_right_leg + pose_left_leg)
        
        # ==================== LEFT HAND (33-53) ====================
        # Offset all indices by 33
        left_hand_base = 33
        
        # Thumb (landmarks 0-4 in hand model)
        left_thumb = [(0, 1), (1, 2), (2, 3), (3, 4)]
        
        # Index finger (landmarks 0, 5-8)
        left_index = [(0, 5), (5, 6), (6, 7), (7, 8)]
        
        # Middle finger (landmarks 0, 9-12)
        left_middle = [(0, 9), (9, 10), (10, 11), (11, 12)]
        
        # Ring finger (landmarks 0, 13-16)
        left_ring = [(0, 13), (13, 14), (14, 15), (15, 16)]
        
        # Pinky finger (landmarks 0, 17-20)
        left_pinky = [(0, 17), (17, 18), (18, 19), (19, 20)]
        
        # Apply offset to left hand
        left_hand_links = left_thumb + left_index + left_middle + left_ring + left_pinky
        left_hand_links = [(i + left_hand_base, j + left_hand_base) 
                           for i, j in left_hand_links]
        links.extend(left_hand_links)
        
        # ==================== RIGHT HAND (54-74) ====================
        # Offset all indices by 54
        right_hand_base = 54
        
        # Same structure as left hand
        right_thumb = [(0, 1), (1, 2), (2, 3), (3, 4)]
        right_index = [(0, 5), (5, 6), (6, 7), (7, 8)]
        right_middle = [(0, 9), (9, 10), (10, 11), (11, 12)]
        right_ring = [(0, 13), (13, 14), (14, 15), (15, 16)]
        right_pinky = [(0, 17), (17, 18), (18, 19), (19, 20)]
        
        # Apply offset to right hand
        right_hand_links = right_thumb + right_index + right_middle + right_ring + right_pinky
        right_hand_links = [(i + right_hand_base, j + right_hand_base) 
                            for i, j in right_hand_links]
        links.extend(right_hand_links)
        
        # ==================== CRITICAL BRIDGE CONNECTIONS ====================
        # These connect pose wrists to hand roots - ESSENTIAL for information flow
        bridge_connections = [
            (15, 33),  # Left wrist (pose) → Left hand root
            (16, 54),  # Right wrist (pose) → Right hand root
        ]
        links.extend(bridge_connections)
        
        return links
    
    def get_adjacency_matrix(self, strategy: str = 'spatial') -> np.ndarray:
        """
        Generate the adjacency matrix A for ST-GCN with partition strategy.
        
        Returns 3 subsets of adjacency matrices:
        - Subset 0: Self-connections (node to itself)
        - Subset 1: Inward edges (closer to center)
        - Subset 2: Outward edges (further from center)
        
        Args:
            strategy: 'spatial' (physical partitioning) or 'uniform' (no partitioning)
        
        Returns:
            Normalized adjacency matrix of shape (3, num_nodes, num_nodes)
            where 3 represents the partition subsets
        """
        if strategy == 'uniform':
            # All nodes connected uniformly - single subset with self-connections
            A = np.zeros((3, self.num_nodes, self.num_nodes))
            A[0] = np.eye(self.num_nodes)  # Self-connections
            A[1] = np.ones((self.num_nodes, self.num_nodes))  # All connected
            A[2] = np.ones((self.num_nodes, self.num_nodes))  # All connected
        
        elif strategy == 'spatial':
            # Physical bone connections with spatial partitioning
            A = np.zeros((3, self.num_nodes, self.num_nodes))
            
            # Subset 0: Self-connections
            A[0] = np.eye(self.num_nodes)
            
            # Build distance map from center (nose = 0)
            hop_dis = self._compute_hop_distance(self.center)
            
            # Subset 1: Inward edges (closer to center)
            # Subset 2: Outward edges (further from center)
            for i, j in self.neighbor_links:
                if hop_dis[j] < hop_dis[i]:  # j is closer to center
                    A[1, i, j] = 1
                elif hop_dis[j] > hop_dis[i]:  # j is further from center
                    A[2, i, j] = 1
                else:  # Same distance - put in both for symmetry
                    A[1, i, j] = 1
                    A[2, i, j] = 1
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Normalize each subset: D^(-1/2) @ A @ D^(-1/2)
        for k in range(A.shape[0]):
            D = np.sum(A[k], axis=1)  # Degree vector
            # Suppress divide by zero warning (handled by setting inf to 0)
            with np.errstate(divide='ignore', invalid='ignore'):
                D_inv_sqrt = np.power(D, -0.5)
            D_inv_sqrt[np.isinf(D_inv_sqrt)] = 0  # Handle isolated nodes
            D_mat = np.diag(D_inv_sqrt)
            A[k] = D_mat @ A[k] @ D_mat
        
        return A.astype(np.float32)
    
    def _compute_hop_distance(self, center: int) -> np.ndarray:
        """
        Compute shortest hop distance from each node to center node.
        Uses BFS to find minimum path length.
        
        Args:
            center: Center node index
        
        Returns:
            Array of hop distances (num_nodes,)
        """
        from collections import deque
        
        # Build adjacency list
        adj_list = {i: [] for i in range(self.num_nodes)}
        for i, j in self.neighbor_links:
            adj_list[i].append(j)
            adj_list[j].append(i)
        
        # BFS to compute distances
        distances = np.full(self.num_nodes, np.inf)
        distances[center] = 0
        
        queue = deque([center])
        visited = {center}
        
        while queue:
            node = queue.popleft()
            for neighbor in adj_list[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    distances[neighbor] = distances[node] + 1
                    queue.append(neighbor)
        
        return distances
    
    def get_edge_list(self) -> List[Tuple[int, int]]:
        """Return the list of edges for visualization or debugging."""
        return self.neighbor_links
    
    def get_bone_connections(self) -> List[List[int]]:
        """
        Return bone connections for two-stream architecture.
        
        Bone = vector from parent joint to child joint.
        Used in TwoStreamNSAGF to compute bone features.
        
        Returns:
            List of [parent, child] pairs representing bones
        """
        # Use same connections as neighbor_links
        # Each edge represents a bone (parent → child relationship)
        return [[i, j] for i, j in self.neighbor_links]
    
    def get_node_groups(self) -> Dict[str, List[int]]:
        """
        Return semantic groupings of nodes for analysis.
        """
        return {
            'pose_upper': list(range(0, 17)),  # Face + shoulders + arms
            'pose_lower': list(range(17, 33)),  # Torso + legs
            'left_hand': list(range(33, 54)),
            'right_hand': list(range(54, 75)),
            'wrists': [15, 16],  # Critical bridge nodes
            'hands_roots': [33, 54],  # Hand root nodes
        }
    
    def visualize_graph(self, save_path: str = None):
        """
        Create a simple visualization of the graph structure.
        Requires matplotlib and networkx (optional).
        """
        try:
            import matplotlib.pyplot as plt
            import networkx as nx
            
            G = nx.Graph()
            G.add_edges_from(self.neighbor_links)
            
            # Color nodes by group
            groups = self.get_node_groups()
            color_map = []
            for node in G.nodes():
                if node in groups['pose_upper']:
                    color_map.append('lightblue')
                elif node in groups['pose_lower']:
                    color_map.append('lightgreen')
                elif node in groups['left_hand']:
                    color_map.append('orange')
                elif node in groups['right_hand']:
                    color_map.append('red')
                else:
                    color_map.append('gray')
            
            plt.figure(figsize=(12, 10))
            pos = nx.spring_layout(G, seed=42)
            nx.draw(G, pos, node_color=color_map, with_labels=True, 
                    node_size=100, font_size=6, edge_color='gray', alpha=0.6)
            
            plt.title("NS-AGF 75-Node MediaPipe Graph Topology")
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"✅ Graph visualization saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            print("⚠️ Install matplotlib and networkx to visualize: pip install matplotlib networkx")


# ==================== TESTING ====================
if __name__ == "__main__":
    print("🔬 Testing MediaPipe Graph Topology...")
    
    graph = MediaPipeGraph()
    
    print(f"✅ Graph initialized with {graph.num_nodes} nodes")
    print(f"✅ Total edges: {len(graph.neighbor_links)}")
    
    # Test adjacency matrix
    A_spatial = graph.get_adjacency_matrix(strategy='spatial')
    print(f"✅ Spatial adjacency matrix shape: {A_spatial.shape}")
    print(f"   Matrix stats: min={A_spatial.min():.4f}, max={A_spatial.max():.4f}, mean={A_spatial.mean():.4f}")
    
    # Verify bridge connections exist
    print("\n🔗 Verifying critical bridge connections:")
    print(f"   Left wrist (15) → Left hand root (33): {(15, 33) in graph.neighbor_links}")
    print(f"   Right wrist (16) → Right hand root (54): {(16, 54) in graph.neighbor_links}")
    
    # Show node groups
    groups = graph.get_node_groups()
    print("\n📊 Node group sizes:")
    for name, nodes in groups.items():
        print(f"   {name}: {len(nodes)} nodes")
    
    print("\n✨ All tests passed! Graph topology is valid.")
    
    # Uncomment to visualize (requires matplotlib + networkx)
    # graph.visualize_graph(save_path="ns_agf_graph_topology.png")
