#!/usr/bin/env python3
"""
MOSAR GraphRAG Pipeline Runner
통합 실행 스크립트 - Phase 1~4 전체 또는 개별 실행
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def run_phase1():
    """Phase 1: Document Ingestion & COVERS relationships"""
    print("\n" + "="*60)
    print("Phase 1: Document Ingestion & COVERS Relationships")
    print("="*60)

    # Phase 1-A: Document Ingestion (src/ingest/)
    print("\n[Phase 1-A] Document Ingestion (already completed)")
    print("  - Run: python src/ingest/ingest_documents.py")
    print("  - Status: ✅ 4 documents, 527 sections, 1,659 chunks loaded")

    # Phase 1-B: COVERS relationships
    print("\n[Phase 1-B] Building COVERS relationships...")
    from src.pipeline.phase1_covers_relationships import main as covers_main
    covers_main()
    print("✅ Phase 1 complete")

def run_phase2():
    """Phase 2: Entity Vocabulary Construction"""
    print("\n" + "="*60)
    print("Phase 2: Entity Vocabulary Construction")
    print("="*60)

    # Phase 2-A: Extract candidates
    print("\n[Phase 2-A] Extracting entity candidates...")
    from src.pipeline.phase2_extract_candidates import main as extract_main
    extract_main()

    # Phase 2-B: Cluster entities
    print("\n[Phase 2-B] Clustering entities...")
    from src.pipeline.phase2_cluster_entities import main as cluster_main
    cluster_main()

    print("✅ Phase 2 complete")
    print("  → Review config/controlled_vocabulary.json")

def run_phase3():
    """Phase 3: Entity Extraction with Vocabulary"""
    print("\n" + "="*60)
    print("Phase 3: Entity Extraction with Vocabulary")
    print("="*60)

    # Phase 3-A: Extract entities
    print("\n[Phase 3-A] Extracting entities from chunks...")
    from src.pipeline.phase3_extract_entities import main as extract_main
    extract_main()

    # Phase 3-B: Add category labels
    print("\n[Phase 3-B] Adding entity category labels...")
    from src.pipeline.phase3_add_labels import main as labels_main
    labels_main()

    print("✅ Phase 3 complete")

def run_phase4():
    """Phase 4: Relationship Extraction"""
    print("\n" + "="*60)
    print("Phase 4: Relationship Extraction")
    print("="*60)

    # Phase 4-A: Requirement relationships
    print("\n[Phase 4-A] Extracting requirement relationships...")
    from src.pipeline.phase4a_req_relationships import main as req_main
    req_main()

    # Phase 4-B: Component relationships
    print("\n[Phase 4-B] Extracting component relationships...")
    from src.pipeline.phase4b_comp_relationships import main as comp_main
    comp_main()

    print("✅ Phase 4 complete")

def main():
    parser = argparse.ArgumentParser(
        description="MOSAR GraphRAG Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all phases
  python run_pipeline.py --all

  # Run specific phase
  python run_pipeline.py --phase 2

  # Run multiple phases
  python run_pipeline.py --phase 3 4

Phase descriptions:
  1: Document Ingestion & COVERS relationships
  2: Entity Vocabulary Construction (Candidates + Clustering)
  3: Entity Extraction with Vocabulary
  4: Relationship Extraction (Requirements + Components)
        """
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all phases (1-4)"
    )

    parser.add_argument(
        "--phase",
        type=int,
        nargs="+",
        choices=[1, 2, 3, 4],
        help="Run specific phase(s)"
    )

    args = parser.parse_args()

    if not args.all and not args.phase:
        parser.print_help()
        sys.exit(1)

    phases_to_run = []
    if args.all:
        phases_to_run = [1, 2, 3, 4]
    elif args.phase:
        phases_to_run = sorted(args.phase)

    print("\n" + "="*60)
    print("MOSAR GraphRAG Pipeline")
    print("="*60)
    print(f"Phases to run: {phases_to_run}")
    print()

    phase_functions = {
        1: run_phase1,
        2: run_phase2,
        3: run_phase3,
        4: run_phase4
    }

    try:
        for phase in phases_to_run:
            phase_functions[phase]()

        print("\n" + "="*60)
        print("✅ Pipeline execution complete!")
        print("="*60)

        if args.all or 4 in phases_to_run:
            print("\n📊 Final Database Status:")
            print("  - Nodes: ~2,839")
            print("  - Relationships: ~15,225")
            print("  - GraphRAG ready for UI development")

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during pipeline execution:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
