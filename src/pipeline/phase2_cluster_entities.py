"""
Stage 3-A Phase 2: Entity Clustering & Vocabulary Construction

Phase 1에서 추출한 entity candidates를 clustering하여
canonical names를 결정하고 vocabulary를 구축합니다.
"""
import sys
import io
import os
import json
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load environment
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-ada-002"


def get_embedding(text: str) -> List[float]:
    """텍스트의 embedding을 생성합니다."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding for '{text}': {e}")
        return None


def cluster_entities(entity_names: List[str], embeddings: np.ndarray, threshold: float = 0.85) -> List[List[int]]:
    """
    Hierarchical clustering을 사용하여 유사한 entity들을 그룹화합니다.

    Args:
        entity_names: Entity 이름 리스트
        embeddings: Entity embeddings (N x 1536)
        threshold: Similarity threshold (0.85 = 85% similar)

    Returns:
        Cluster 인덱스 리스트
    """
    # Cosine similarity를 distance로 사용
    # distance = 1 - cosine_similarity
    distance_threshold = 1 - threshold

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric='cosine',
        linkage='average'
    )

    labels = clustering.fit_predict(embeddings)

    # Group by cluster label
    clusters = defaultdict(list)
    for idx, label in enumerate(labels):
        clusters[label].append(idx)

    return list(clusters.values())


def suggest_canonical_name(cluster_indices: List[int], entity_names: List[str], entity_counts: List[int]) -> Tuple[str, bool]:
    """
    Cluster의 canonical name을 제안합니다.

    전략:
    1. 가장 많이 등장한 이름 선택
    2. 동률이면 가장 짧은 이름 선택
    3. 너무 일반적인 이름("the module" 등)은 제외

    Returns:
        (suggested_canonical_name, needs_human_review)
    """
    # Get names and counts for this cluster
    cluster_names = [(entity_names[i], entity_counts[i]) for i in cluster_indices]

    # Sort by count (desc), then by length (asc)
    cluster_names.sort(key=lambda x: (-x[1], len(x[0])))

    # Check if top choice is generic
    top_choice = cluster_names[0][0]
    generic_patterns = ["the ", "a ", "an ", "module", "system", "component"]

    is_generic = any(pattern in top_choice.lower() for pattern in generic_patterns)

    # If generic, try to find a more specific name
    if is_generic and len(cluster_names) > 1:
        for name, count in cluster_names[1:]:
            if not any(pattern in name.lower() for pattern in generic_patterns):
                top_choice = name
                is_generic = False
                break

    # Check if human review is needed
    needs_review = False

    # Review needed if:
    # 1. Generic name
    # 2. Large cluster (>5 variants) - might be over-clustering
    # 3. Very different counts (might be different entities)
    if is_generic:
        needs_review = True
    elif len(cluster_names) > 5:
        needs_review = True
    elif len(cluster_names) > 1:
        max_count = cluster_names[0][1]
        min_count = cluster_names[-1][1]
        if max_count > min_count * 10:  # 10x difference
            needs_review = True

    return top_choice, needs_review


def build_entity_clusters(aggregated_data: Dict, category: str, threshold: float = 0.85) -> List[Dict]:
    """
    특정 category의 entity들을 clustering합니다.

    Returns:
        List of cluster dicts with structure:
        {
            "cluster_id": int,
            "variants": [str, ...],
            "counts": [int, ...],
            "suggested_canonical": str,
            "human_review_needed": bool
        }
    """
    entities = aggregated_data[category]

    if len(entities) == 0:
        return []

    print(f"\n  Processing {category}...")
    print(f"    Total unique variants: {len(entities)}")

    # Prepare data
    entity_names = list(entities.keys())
    entity_counts = [entities[name]["count"] for name in entity_names]

    # Generate embeddings
    print(f"    Generating embeddings...")
    embeddings_list = []

    for name in entity_names:
        emb = get_embedding(name)
        if emb is None:
            emb = [0.0] * 1536  # Fallback
        embeddings_list.append(emb)

    embeddings = np.array(embeddings_list)

    # Cluster
    print(f"    Clustering (threshold={threshold})...")
    cluster_indices = cluster_entities(entity_names, embeddings, threshold)

    print(f"    Found {len(cluster_indices)} clusters")

    # Build cluster results
    clusters = []

    for cluster_id, indices in enumerate(cluster_indices):
        # Get names and counts for this cluster
        variants = [entity_names[i] for i in indices]
        counts = [entity_counts[i] for i in indices]

        # Sort by count descending
        sorted_pairs = sorted(zip(variants, counts), key=lambda x: -x[1])
        variants = [p[0] for p in sorted_pairs]
        counts = [p[1] for p in sorted_pairs]

        # Suggest canonical name
        canonical, needs_review = suggest_canonical_name(indices, entity_names, entity_counts)

        clusters.append({
            "cluster_id": cluster_id,
            "variants": variants,
            "counts": counts,
            "suggested_canonical": canonical,
            "human_review_needed": needs_review
        })

    # Sort clusters by total count (most mentioned first)
    clusters.sort(key=lambda c: sum(c["counts"]), reverse=True)

    # Re-assign cluster IDs after sorting
    for i, cluster in enumerate(clusters):
        cluster["cluster_id"] = i

    return clusters


def generate_vocabulary_template(all_clusters: Dict) -> Dict:
    """
    Cluster 결과를 vocabulary 템플릿으로 변환합니다.

    Returns:
        Entity vocabulary JSON structure
    """
    vocabulary = {}

    for category, clusters in all_clusters.items():
        vocabulary[category] = []

        for cluster in clusters:
            canonical = cluster["suggested_canonical"]
            variants = cluster["variants"]

            # Aliases는 canonical을 제외한 나머지
            aliases = [v for v in variants if v != canonical]

            entry = {
                "canonical_name": canonical,
                "full_name": canonical,  # 수동으로 수정 가능
                "aliases": aliases,
                "type": "HW" if category == "components" else None,  # 수동으로 수정
                "total_mentions": sum(cluster["counts"]),
                "variants_count": len(variants),
                "human_review_needed": cluster["human_review_needed"]
            }

            vocabulary[category].append(entry)

    return vocabulary


def print_cluster_statistics(all_clusters: Dict):
    """Clustering 결과 통계 출력"""
    print("\n" + "="*100)
    print("  CLUSTERING STATISTICS")
    print("="*100)

    for category, clusters in all_clusters.items():
        print(f"\n{category.upper()}:")
        print(f"  Clusters: {len(clusters)}")

        total_variants = sum(len(c["variants"]) for c in clusters)
        print(f"  Total variants: {total_variants}")

        needs_review = sum(1 for c in clusters if c["human_review_needed"])
        print(f"  Needs human review: {needs_review} ({100*needs_review/len(clusters):.1f}%)")

        # Top 5 clusters
        print(f"\n  Top 5 clusters:")
        for cluster in clusters[:5]:
            canonical = cluster["suggested_canonical"]
            total_mentions = sum(cluster["counts"])
            variant_count = len(cluster["variants"])
            review_flag = " [REVIEW]" if cluster["human_review_needed"] else ""

            print(f"    {canonical}: {total_mentions} mentions, {variant_count} variants{review_flag}")

            if variant_count > 1:
                # Show top 3 variants
                for var, count in zip(cluster["variants"][:3], cluster["counts"][:3]):
                    print(f"      - {var}: {count}")


def main():
    print("="*100)
    print("  Stage 3-A Phase 2: Entity Clustering & Vocabulary Construction")
    print("="*100)

    # Load Phase 1 results
    print("\n[1] Loading entity candidates from Phase 1...")

    input_file = "output/entity_candidates_raw.json"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        print("Please run extract_entity_candidates.py first (Phase 1)")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        aggregated_data = json.load(f)

    # Cluster each category
    print("\n[2] Clustering entities by category...")

    all_clusters = {}
    threshold = 0.85  # 85% similarity threshold

    for category in ["components", "scenarios", "test_cases", "subsystems", "interfaces"]:
        clusters = build_entity_clusters(aggregated_data, category, threshold)
        all_clusters[category] = clusters

    # Save cluster results
    print("\n[3] Saving cluster results...")

    output_file = "output/entity_clusters.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_clusters, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {output_file}")

    # Generate vocabulary template
    print("\n[4] Generating vocabulary template...")

    vocabulary = generate_vocabulary_template(all_clusters)

    vocab_file = "output/entity_vocabulary_draft.json"
    with open(vocab_file, "w", encoding="utf-8") as f:
        json.dump(vocabulary, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {vocab_file}")

    # Print statistics
    print_cluster_statistics(all_clusters)

    print("\n" + "="*100)
    print("  Phase 2 Complete!")
    print("="*100)
    print(f"\nNext steps:")
    print(f"1. Review: {vocab_file}")
    print(f"   - Check 'human_review_needed' items")
    print(f"   - Adjust canonical names if needed")
    print(f"   - Remove unwanted variants from aliases")
    print(f"   - Add 'full_name' for each entity")
    print(f"2. Save final version as: config/entity_vocabulary.json")
    print(f"3. Run: extract_entities_with_vocab.py (Phase 3)")


if __name__ == "__main__":
    main()
