"""Streamlit dashboard for factor leaderboard, curves, IC timeline, regime panel, post-mortems."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import json

from ..memory.store import ExperimentStore
from ..viz.plots import (
    plot_equity_curve, plot_drawdown, plot_ic_timeline,
    plot_ic_histogram, plot_regime_heatmap, plot_factor_leaderboard
)


# Page config
st.set_page_config(
    page_title="Alpha-Mining Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'store' not in st.session_state:
    st.session_state.store = ExperimentStore("experiments.db")


@st.cache_data
def load_runs_data():
    """Load runs data from database."""
    store = st.session_state.store
    top_runs = store.get_top_runs(limit=100, order_by="sharpe")
    
    runs_data = []
    for run in top_runs:
        factor = store.get_factor(run.factor_id)
        metrics = run.metrics[0] if run.metrics else None
        
        if metrics:
            runs_data.append({
                'run_id': run.id,
                'factor_id': run.factor_id,
                'factor_name': factor.name if factor else 'Unknown',
                'sharpe': metrics.sharpe,
                'maxdd': metrics.maxdd,
                'avg_ic': metrics.avg_ic,
                'ir': metrics.ir,
                'turnover_monthly': metrics.turnover_monthly,
                'ann_ret': metrics.ann_ret,
                'ann_vol': metrics.ann_vol,
                'hit_rate': metrics.hit_rate,
                'regime': run.regime_label,
                'start_date': run.start_date,
                'end_date': run.end_date,
                'n_issues': len(run.issues)
            })
    
    return pd.DataFrame(runs_data)


def main():
    """Main dashboard function."""
    st.title("📈 Alpha-Mining LLM Agent Framework Dashboard")
    
    # Load data
    runs_df = load_runs_data()
    
    if len(runs_df) == 0:
        st.warning("No runs found in database. Run some backtests first!")
        return
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    min_sharpe = st.sidebar.slider("Min Sharpe", 0.0, 3.0, 0.0, 0.1)
    max_maxdd = st.sidebar.slider("Max Drawdown", 0.0, 1.0, 1.0, 0.05)
    min_ic = st.sidebar.slider("Min Avg IC", -0.1, 0.2, -0.1, 0.01)
    
    # Apply filters
    filtered_df = runs_df[
        (runs_df['sharpe'] >= min_sharpe) &
        (abs(runs_df['maxdd']) <= max_maxdd) &
        (runs_df['avg_ic'] >= min_ic)
    ]
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Leaderboard", "Performance", "IC Analysis", "Regime Analysis", "Post-Mortems"
    ])
    
    with tab1:
        st.header("Factor Leaderboard")
        
        # Sort options
        sort_by = st.selectbox("Sort by", ["sharpe", "avg_ic", "ir", "ann_ret"], index=0)
        ascending = st.checkbox("Ascending", False)
        
        display_df = filtered_df.sort_values(sort_by, ascending=ascending)
        
        # Display table
        st.dataframe(
            display_df[['factor_name', 'sharpe', 'maxdd', 'avg_ic', 'ir', 
                       'turnover_monthly', 'ann_ret', 'ann_vol', 'hit_rate', 'n_issues']].head(20),
            use_container_width=True
        )
        
        # Leaderboard chart
        if len(display_df) > 0:
            leaderboard_data = display_df.head(10).to_dict('records')
            fig = plot_factor_leaderboard(leaderboard_data)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Performance Analysis")
        
        if len(filtered_df) == 0:
            st.warning("No runs match the filters.")
        else:
            # Select run
            run_options = filtered_df['factor_name'].tolist()
            selected_factor = st.selectbox("Select Factor", run_options, index=0)
            
            selected_run = filtered_df[filtered_df['factor_name'] == selected_factor].iloc[0]
            run_id = selected_run['run_id']
            
            # Load equity curve if available
            run_dir = Path(f"experiments/runs/run_{run_id}")
            equity_file = run_dir / "equity_curve.parquet"
            
            if equity_file.exists():
                equity_curve = pd.read_parquet(equity_file)['equity']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = plot_equity_curve(equity_curve, title=f"Equity Curve: {selected_factor}")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = plot_drawdown(equity_curve, title=f"Drawdown: {selected_factor}")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Equity curve data not available for this run.")
            
            # Metrics summary
            st.subheader("Metrics Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Sharpe Ratio", f"{selected_run['sharpe']:.2f}")
                st.metric("Max Drawdown", f"{selected_run['maxdd']:.2%}")
            
            with col2:
                st.metric("Avg IC", f"{selected_run['avg_ic']:.4f}")
                st.metric("Information Ratio", f"{selected_run['ir']:.2f}")
            
            with col3:
                st.metric("Ann Return", f"{selected_run['ann_ret']:.2%}")
                st.metric("Ann Volatility", f"{selected_run['ann_vol']:.2%}")
            
            with col4:
                st.metric("Turnover (monthly)", f"{selected_run['turnover_monthly']:.1f}%")
                st.metric("Hit Rate", f"{selected_run['hit_rate']:.2%}")
    
    with tab3:
        st.header("Information Coefficient Analysis")
        
        if len(filtered_df) == 0:
            st.warning("No runs match the filters.")
        else:
            selected_factor = st.selectbox("Select Factor", filtered_df['factor_name'].tolist(), 
                                         key="ic_factor", index=0)
            selected_run = filtered_df[filtered_df['factor_name'] == selected_factor].iloc[0]
            run_id = selected_run['run_id']
            
            # IC timeline (simplified - would need IC series data)
            st.info("IC timeline would be displayed here if IC series data is available.")
            
            # IC statistics
            st.subheader("IC Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average IC", f"{selected_run['avg_ic']:.4f}")
            
            with col2:
                st.metric("Information Ratio", f"{selected_run['ir']:.2f}")
            
            with col3:
                # Would calculate IC std if available
                st.metric("IC Quality", "Good" if selected_run['avg_ic'] > 0.05 else "Needs Improvement")
    
    with tab4:
        st.header("Regime Analysis")
        
        if len(filtered_df) == 0:
            st.warning("No runs match the filters.")
        else:
            # Group by regime
            regime_df = filtered_df.groupby('regime').agg({
                'sharpe': 'mean',
                'avg_ic': 'mean',
                'ann_ret': 'mean',
                'maxdd': 'mean'
            }).reset_index()
            
            if len(regime_df) > 0:
                st.dataframe(regime_df, use_container_width=True)
                
                # Regime heatmap
                performance_by_regime = {}
                for _, row in regime_df.iterrows():
                    performance_by_regime[row['regime'] or 'unknown'] = {
                        'sharpe': row['sharpe'],
                        'avg_ic': row['avg_ic'],
                        'return': row['ann_ret'],
                        'maxdd': abs(row['maxdd'])
                    }
                
                fig = plot_regime_heatmap(performance_by_regime)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No regime data available.")
    
    with tab5:
        st.header("Post-Mortems & Lessons")
        
        store = st.session_state.store
        
        # Get lessons
        from ..memory.lessons import LessonManager
        lesson_manager = LessonManager(store)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Success Stories")
            success_lessons = lesson_manager.get_success_ledger(limit=10)
            
            for lesson in success_lessons:
                with st.expander(f"✓ {lesson.title}"):
                    st.write(lesson.body[:500] + "...")
                    st.caption(f"Tags: {', '.join(lesson.tags or [])}")
        
        with col2:
            st.subheader("Failure Analysis")
            failure_lessons = lesson_manager.get_error_bank(limit=10)
            
            for lesson in failure_lessons:
                with st.expander(f"✗ {lesson.title}"):
                    st.write(lesson.body[:500] + "...")
                    st.caption(f"Tags: {', '.join(lesson.tags or [])}")
        
        # Run details
        st.subheader("Run Details")
        selected_run_id = st.selectbox(
            "Select Run ID",
            filtered_df['run_id'].tolist(),
            key="postmortem_run"
        )
        
        if selected_run_id:
            run = store.get_session().query(store.Run).filter(store.Run.id == selected_run_id).first()
            if run:
                factor = store.get_factor(run.factor_id)
                metrics = run.metrics[0] if run.metrics else None
                issues = run.issues
                
                st.write(f"**Factor:** {factor.name if factor else 'Unknown'}")
                st.write(f"**Date Range:** {run.start_date.date()} to {run.end_date.date()}")
                
                if metrics:
                    st.write(f"**Sharpe:** {metrics.sharpe:.2f}")
                    st.write(f"**MaxDD:** {metrics.maxdd:.2%}")
                
                if issues:
                    st.write("**Issues:**")
                    for issue in issues:
                        st.write(f"- **{issue.type}** ({issue.severity}): {issue.detail}")


if __name__ == "__main__":
    main()

