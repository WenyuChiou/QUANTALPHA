"""MCP tool: Write lesson to database and vector index."""

from typing import Dict, Any, Optional, List
from pathlib import Path

from ..memory.store import ExperimentStore
from ..memory.lessons import LessonManager
from ..rag.indexer import KnowledgeBaseIndexer


def write_lesson(
    title: str,
    body: str,
    tags: Optional[List[str]] = None,
    source_run_id: Optional[int] = None,
    lesson_type: str = "general",
    metadata: Optional[Dict[str, Any]] = None,
    db_path: str = "experiments.db",
    kb_dir: Path = Path("kb"),
    index_path: str = "./kb.index"
) -> Dict[str, Any]:
    """Write a lesson to database and index it in vector DB.
    
    Args:
        title: Lesson title
        body: Lesson body text
        tags: List of tags
        source_run_id: Source run ID
        lesson_type: Type (success, failure, general)
        metadata: Additional metadata
        db_path: Database path
        kb_dir: Knowledge base directory
        index_path: Vector index path
    
    Returns:
        Dictionary with lesson_id and status
    """
    store = ExperimentStore(db_path)
    lesson_manager = LessonManager(store)
    
    # Create lesson in database
    lesson = store.create_lesson(
        title=title,
        body=body,
        tags=tags or [],
        source_run_id=source_run_id,
        lesson_type=lesson_type,
        metadata=metadata or {}
    )
    
    # Write to knowledge base file
    kb_dir.mkdir(parents=True, exist_ok=True)
    
    if lesson_type == "success":
        subdir = kb_dir / "run_summaries"
    elif lesson_type == "failure":
        subdir = kb_dir / "run_summaries"
    else:
        subdir = kb_dir / "notes"
    
    subdir.mkdir(parents=True, exist_ok=True)
    
    # Create markdown file
    filename = f"lesson_{lesson.id}_{title.replace(' ', '_').lower()}.md"
    file_path = subdir / filename
    
    content = f"""# {title}

## Metadata
- Lesson ID: {lesson.id}
- Type: {lesson_type}
- Source Run ID: {source_run_id or 'N/A'}
- Tags: {', '.join(tags or [])}

## Content

{body}

## Metadata (JSON)
```json
{metadata or {}}
```
"""
    
    file_path.write_text(content, encoding='utf-8')
    
    # Index in vector DB
    try:
        indexer = KnowledgeBaseIndexer(kb_dir=kb_dir, index_path=index_path)
        
        # Determine topic from tags
        topic = "general"
        if tags:
            if "momentum" in tags:
                topic = "momentum"
            elif "volatility" in tags:
                topic = "volatility"
            elif "factor" in tags:
                topic = "factor_design"
        
        indexer.index_file(
            file_path=file_path,
            topic=topic,
            status=lesson_type,
            subdir=subdir.name
        )
    except Exception as e:
        print(f"Warning: Failed to index lesson: {e}")
    
    return {
        'lesson_id': lesson.id,
        'file_path': str(file_path),
        'status': 'success'
    }

