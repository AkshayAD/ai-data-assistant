import streamlit as st
import pandas as pd
import os
import json
from src.utils import configure_genai, get_gemini_response, process_csv_file, generate_data_profile_summary

# Page configuration
st.set_page_config(
    page_title="AI Data Analysis Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure Gemini API
configure_genai()

# Initialize session state variables if they don't exist
if 'project_initialized' not in st.session_state:
    st.session_state.project_initialized = False
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'data_uploaded' not in st.session_state:
    st.session_state.data_uploaded = False
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'data_profiles' not in st.session_state:
    st.session_state.data_profiles = {}
if 'manager_plan' not in st.session_state:
    st.session_state.manager_plan = None
if 'analyst_summary' not in st.session_state:
    st.session_state.analyst_summary = None
if 'associate_guidance' not in st.session_state:
    st.session_state.associate_guidance = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []
if 'final_report' not in st.session_state:
    st.session_state.final_report = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Function to reset the session state
def reset_session():
    st.session_state.project_initialized = False
    st.session_state.current_step = 0
    st.session_state.data_uploaded = False
    st.session_state.dataframes = {}
    st.session_state.data_profiles = {}
    st.session_state.manager_plan = None
    st.session_state.analyst_summary = None
    st.session_state.associate_guidance = None
    st.session_state.analysis_results = []
    st.session_state.final_report = None
    st.session_state.conversation_history = []

# Add a message to the conversation history
def add_to_conversation(role, content):
    st.session_state.conversation_history.append({
        "role": role,
        "content": content
    })

# Main application
def main():
    # Sidebar
    with st.sidebar:
        st.title("AI Data Analysis Assistant")
        st.markdown("---")
        
        # Project navigation
        st.subheader("Navigation")
        
        if st.session_state.project_initialized:
            step_options = [
                "1. Project Setup",
                "2. Manager Planning",
                "3. Data Understanding",
                "4. Analysis Guidance",
                "5. Analysis Execution",
                "6. Final Report"
            ]
            selected_step = st.selectbox("Go to step:", step_options, index=st.session_state.current_step)
            st.session_state.current_step = step_options.index(selected_step)
            
            if st.button("Reset Project"):
                reset_session()
                st.experimental_rerun()
        
        st.markdown("---")
        st.markdown("### AI Team")
        st.markdown("🧠 **Manager**: Creates analysis plan")
        st.markdown("📊 **Analyst**: Examines data details")
        st.markdown("🔍 **Associate**: Guides analysis execution")
    
    # Main content area
    if not st.session_state.project_initialized:
        # Step 1: Project Setup
        st.title("🚀 Start a New Data Analysis Project")
        
        with st.form("project_setup_form"):
            st.subheader("Project Details")
            project_name = st.text_input("Project Name")
            problem_statement = st.text_area("Problem Statement / Goal", 
                                            placeholder="Describe what you want to learn from your data...")
            data_context = st.text_area("Data Context (Optional)", 
                                       placeholder="Provide any background information about your data...")
            
            st.subheader("Upload Data")
            uploaded_files = st.file_uploader("Upload CSV Files", type=["csv"], accept_multiple_files=True)
            
            submit_button = st.form_submit_button("Start Analysis")
            
            if submit_button:
                if not project_name or not problem_statement or not uploaded_files:
                    st.error("Please provide a project name, problem statement, and at least one CSV file.")
                else:
                    # Process uploaded files
                    with st.spinner("Processing data files..."):
                        for uploaded_file in uploaded_files:
                            df, profile = process_csv_file(uploaded_file)
                            if df is not None:
                                st.session_state.dataframes[uploaded_file.name] = df
                                st.session_state.data_profiles[uploaded_file.name] = profile
                        
                        if st.session_state.dataframes:
                            st.session_state.data_uploaded = True
                            st.session_state.project_initialized = True
                            st.session_state.current_step = 1
                            
                            # Add initial project details to conversation history
                            add_to_conversation("user", f"Project: {project_name}\nProblem Statement: {problem_statement}\nData Context: {data_context}")
                            
                            # Store project details in session state
                            st.session_state.project_name = project_name
                            st.session_state.problem_statement = problem_statement
                            st.session_state.data_context = data_context
                            
                            st.success("Project initialized successfully!")
                            st.experimental_rerun()
    else:
        # Display the current step based on navigation
        if st.session_state.current_step == 0:
            # Project Setup (already completed)
            st.title("Project Setup")
            st.success("Project has been set up successfully!")
            st.write(f"**Project Name:** {st.session_state.project_name}")
            st.write(f"**Problem Statement:** {st.session_state.problem_statement}")
            if st.session_state.data_context:
                st.write(f"**Data Context:** {st.session_state.data_context}")
            
            st.subheader("Uploaded Data Files")
            for file_name in st.session_state.dataframes.keys():
                st.write(f"- {file_name}")
            
            if st.button("Continue to Manager Planning"):
                st.session_state.current_step = 1
                st.experimental_rerun()
                
        elif st.session_state.current_step == 1:
            # Step 2: Manager Planning
            st.title("👨‍💼 AI Manager - Analysis Planning")
            
            if st.session_state.manager_plan is None:
                with st.spinner("AI Manager is creating an analysis plan..."):
                    # Prepare the prompt for the Manager
                    file_info = ""
                    for file_name, profile in st.session_state.data_profiles.items():
                        file_info += f"\nFile: {file_name}\n"
                        file_info += f"- Columns: {', '.join(profile['columns'])}\n"
                        file_info += f"- Dimensions: {profile['shape'][0]} rows × {profile['shape'][1]} columns\n"
                    
                    manager_prompt = f"""
                    Problem Statement: {st.session_state.problem_statement}
                    
                    Data Context: {st.session_state.data_context}
                    
                    Available Data Files: {file_info}
                    
                    Based on this information, create a structured, step-by-step analytical plan. 
                    The plan should cover data understanding, cleaning (if likely needed), 
                    exploratory analysis, specific analyses relevant to the goal, and final synthesis. 
                    Output this plan as a numbered list.
                    """
                    
                    # Get response from Gemini API
                    manager_response = get_gemini_response(manager_prompt, persona="manager")
                    
                    if manager_response:
                        st.session_state.manager_plan = manager_response
                        add_to_conversation("manager", manager_response)
            
            if st.session_state.manager_plan:
                st.markdown("### Analysis Plan")
                st.markdown(st.session_state.manager_plan)
                
                # Allow user to provide feedback
                with st.expander("Provide feedback to the Manager"):
                    manager_feedback = st.text_area("Your feedback:", key="manager_feedback")
                    if st.button("Send Feedback"):
                        if manager_feedback:
                            add_to_conversation("user", f"Feedback on plan: {manager_feedback}")
                            
                            # Process the feedback with Gemini
                            feedback_prompt = f"""
                            Original Analysis Plan: 
                            {st.session_state.manager_plan}
                            
                            User Feedback: 
                            {manager_feedback}
                            
                            Please revise the analysis plan based on this feedback. 
                            Keep the same structured format with numbered steps.
                            """
                            
                            with st.spinner("AI Manager is revising the plan..."):
                                revised_plan = get_gemini_response(feedback_prompt, persona="manager")
                                if revised_plan:
                                    st.session_state.manager_plan = revised_plan
                                    add_to_conversation("manager", revised_plan)
                                    st.success("Plan updated based on your feedback!")
                                    st.experimental_rerun()
                
                if st.button("Continue to Data Understanding"):
                    st.session_state.current_step = 2
                    st.experimental_rerun()
                    
        elif st.session_state.current_step == 2:
            # Step 3: Data Understanding
            st.title("📊 AI Analyst - Data Understanding")
            
            if st.session_state.analyst_summary is None:
                with st.spinner("AI Analyst is examining the data..."):
                    # Generate data profile summaries
                    all_profiles_summary = ""
                    for file_name, profile in st.session_state.data_profiles.items():
                        profile_summary = generate_data_profile_summary(profile)
                        all_profiles_summary += f"\n## {file_name}\n{profile_summary}\n"
                    
                    # Prepare the prompt for the Analyst
                    analyst_prompt = f"""
                    Problem Statement: {st.session_state.problem_statement}
                    
                    Manager's Analysis Plan: 
                    {st.session_state.manager_plan}
                    
                    Data Profile Summary:
                    {all_profiles_summary}
                    
                    Based on this information, provide a comprehensive summary of the data. 
                    Explain the key characteristics, potential challenges, and initial observations 
                    that might be relevant to the analysis plan. Focus on data quality, completeness, 
                    and how well it aligns with the problem statement.
                    """
                    
                    # Get response from Gemini API
                    analyst_response = get_gemini_response(analyst_prompt, persona="analyst")
                    
                    if analyst_response:
                        st.session_state.analyst_summary = analyst_response
                        add_to_conversation("analyst", analyst_response)
            
            if st.session_state.analyst_summary:
                # Display data profiles
                with st.expander("View Data Profiles", expanded=False):
                    for file_name, df in st.session_state.dataframes.items():
                        st.subheader(f"File: {file_name}")
                        st.dataframe(df.head(10))
                        
                        profile = st.session_state.data_profiles[file_name]
                        st.write(f"Dimensions: {profile['shape'][0]} rows × {profile['shape'][1]} columns")
                        
                        # Display missing values
                        missing_values = pd.Series(profile['missing_values'])
                        if missing_values.sum() > 0:
                            st.write("Missing Values:")
                            st.dataframe(missing_values[missing_values > 0])
                
                # Display analyst summary
                st.markdown("### Data Summary")
                st.markdown(st.session_state.analyst_summary)
                
                # Allow user to ask questions
                with st.expander("Ask the Analyst about the data"):
                    analyst_question = st.text_area("Your question:", key="analyst_question")
                    if st.button("Ask Question"):
                        if analyst_question:
                            add_to_conversation("user", f"Question about data: {analyst_question}")
                            
                            # Process the question with Gemini
                            question_prompt = f"""
                            Problem Statement: {st.session_state.problem_statement}
                            
                            Data Profile Summary:
                            {all_profiles_summary}
                            
                            Previous Analysis:
                            {st.session_state.analyst_summary}
                            
                            User Question: 
                            {analyst_question}
                            
                            Please provide a detailed answer to the user's question about the data.
                            """
                            
                            with st.spinner("AI Analyst is thinking..."):
                                analyst_answer = get_gemini_response(question_prompt, persona="analyst")
                                if analyst_answer:
                                    add_to_conversation("analyst", analyst_answer)
                                    st.success("Question answered!")
                                    st.markdown("### Answer")
                                    st.markdown(analyst_answer)
                
                if st.button("Continue to Analysis Guidance"):
                    st.session_state.current_step = 3
                    st.experimental_rerun()
                    
        elif st.session_state.current_step == 3:
            # Step 4: Analysis Guidance
            st.title("🔍 AI Associate - Hypothesis & Guidance")
            
            if st.session_state.associate_guidance is None:
                with st.spinner("AI Associate is formulating analysis guidance..."):
                    # Prepare the prompt for the Associate
                    associate_prompt = f"""
                    Problem Statement: {st.session_state.problem_statement}
                    
                    Manager's Analysis Plan: 
                    {st.session_state.manager_plan}
                    
                    Analyst's Data Summary:
                    {st.session_state.analyst_summary}
                    
                    Based on this information, refine the initial steps of the plan. Define specific 
                    hypotheses to test, identify potential edge cases or data quality issues to check 
                    based on the summary, and formulate a clear storyline for the initial exploration. 
                    
                    Outline the exact next 2-3 analysis tasks for the Analyst (e.g., 'Calculate correlation 
                    matrix for numerical columns', 'Generate frequency counts for categorical columns X and Y', 
                    'Visualize distribution of column Z').
                    """
                    
                    # Get response from Gemini API
                    associate_response = get_gemini_response(associate_prompt, persona="associate")
                    
                    if associate_response:
                        st.session_state.associate_guidance = associate_response
                        add_to_conversation("associate", associate_response)
            
            if st.session_state.associate_guidance:
                st.markdown("### Analysis Guidance")
                st.markdown(st.session_state.associate_guidance)
                
                # Allow user to provide feedback
                with st.expander("Provide feedback to the Associate"):
                    associate_feedback = st.text_area("Your feedback:", key="associate_feedback")
                    if st.button("Send Feedback"):
                        if associate_feedback:
                            add_to_conversation("user", f"Feedback on guidance: {associate_feedback}")
                            
                            # Process the feedback with Gemini
                            feedback_prompt = f"""
                            Original Analysis Guidance: 
                            {st.session_state.associate_guidance}
                            
                            User Feedback: 
                            {associate_feedback}
                            
                            Please revise the analysis guidance based on this feedback. 
                            Keep the same structured format with specific tasks and hypotheses.
                            """
                            
                            with st.spinner("AI Associate is revising the guidance..."):
                                revised_guidance = get_gemini_response(feedback_prompt, persona="associate")
                                if revised_guidance:
                                    st.session_state.associate_guidance = revised_guidance
                                    add_to_conversation("associate", revised_guidance)
                                    st.success("Guidance updated based on your feedback!")
                                    st.experimental_rerun()
                
                if st.button("Continue to Analysis Execution"):
                    st.session_state.current_step = 4
                    st.experimental_rerun()
                    
        elif st.session_state.current_step == 4:
            # Step 5: Analysis Execution
            st.title("📈 AI Analyst - Analysis Execution")
            
            # Extract tasks from associate guidance
            if not st.session_state.analysis_results:
                # This is a simplified extraction - in a real app, you might want more sophisticated parsing
                tasks = st.session_state.associate_guidance.split("\n")
                tasks = [t for t in tasks if t.strip() and not t.startswith("#")]
                
                st.subheader("Analysis Tasks")
                for i, task in enumerate(tasks[:5]):  # Limit to first 5 tasks for simplicity
                    if len(task) > 10:  # Skip very short lines
                        st.write(f"{i+1}. {task}")
                
                st.markdown("---")
                st.subheader("Execute Analysis")
                
                # Allow user to select a task to execute
                task_to_execute = st.text_area("Describe the specific analysis task to execute:", 
                                             placeholder="e.g., Calculate correlation between column X and Y")
                
                if st.button("Execute Task"):
                    if task_to_execute:
                        with st.spinner("AI Analyst is executing the task..."):
                            # Prepare data snippet for the task
                            # For simplicity, we'll just use the first dataframe
                            file_name = list(st.session_state.dataframes.keys())[0]
                            df = st.session_state.dataframes[file_name]
                            
                            # Convert a small sample to JSON for the prompt
                            data_sample = df.head(5).to_json(orient="records")
                            
                            # Prepare the prompt for the Analyst
                            task_prompt = f"""
                            Problem Statement: {st.session_state.problem_statement}
                            
                            Analysis Task: {task_to_execute}
                            
                            Data Sample (first 5 rows from {file_name}): 
                            {data_sample}
                            
                            Available Columns: {', '.join(df.columns)}
                            
                            Please execute this analysis task. Provide:
                            1. A clear explanation of the approach
                            2. The Python code you would use (using pandas)
                            3. The results of the analysis
                            4. Key insights derived from the results
                            
                            If the task requires visualization, describe what the visualization would show.
                            """
                            
                            # Get response from Gemini API
                            analysis_result = get_gemini_response(task_prompt, persona="analyst")
                            
                            if analysis_result:
                                # Store the result
                                result_entry = {
                                    "task": task_to_execute,
                                    "result": analysis_result
                                }
                                st.session_state.analysis_results.append(result_entry)
                                add_to_conversation("analyst", f"Task: {task_to_execute}\n\n{analysis_result}")
                                
                                st.success("Analysis task completed!")
                                st.experimental_rerun()
            
            # Display previous analysis results
            if st.session_state.analysis_results:
                st.subheader("Completed Analyses")
                
                for i, result in enumerate(st.session_state.analysis_results):
                    with st.expander(f"Analysis {i+1}: {result['task']}", expanded=(i == len(st.session_state.analysis_results)-1)):
                        st.markdown(result['result'])
                
                # Option to execute another task
                st.markdown("---")
                st.subheader("Execute Another Analysis")
                
                new_task = st.text_area("Describe the next analysis task:", key="new_task",
                                      placeholder="e.g., Analyze the distribution of column Z")
                
                if st.button("Execute New Task"):
                    if new_task:
                        with st.spinner("AI Analyst is executing the task..."):
                            # Similar to above, prepare data and prompt
                            file_name = list(st.session_state.dataframes.keys())[0]
                            df = st.session_state.dataframes[file_name]
                            data_sample = df.head(5).to_json(orient="records")
                            
                            task_prompt = f"""
                            Problem Statement: {st.session_state.problem_statement}
                            
                            Previous Analysis Results:
                            {json.dumps([r['task'] for r in st.session_state.analysis_results])}
                            
                            New Analysis Task: {new_task}
                            
                            Data Sample (first 5 rows from {file_name}): 
                            {data_sample}
                            
                            Available Columns: {', '.join(df.columns)}
                            
                            Please execute this analysis task. Provide:
                            1. A clear explanation of the approach
                            2. The Python code you would use (using pandas)
                            3. The results of the analysis
                            4. Key insights derived from the results
                            
                            If the task requires visualization, describe what the visualization would show.
                            """
                            
                            # Get response from Gemini API
                            analysis_result = get_gemini_response(task_prompt, persona="analyst")
                            
                            if analysis_result:
                                # Store the result
                                result_entry = {
                                    "task": new_task,
                                    "result": analysis_result
                                }
                                st.session_state.analysis_results.append(result_entry)
                                add_to_conversation("analyst", f"Task: {new_task}\n\n{analysis_result}")
                                
                                st.success("Analysis task completed!")
                                st.experimental_rerun()
                
                # Associate review of results
                if len(st.session_state.analysis_results) >= 2:
                    st.markdown("---")
                    st.subheader("AI Associate Review")
                    
                    if st.button("Get Associate's Review of Results"):
                        with st.spinner("AI Associate is reviewing the results..."):
                            # Prepare the prompt for the Associate
                            results_summary = ""
                            for i, result in enumerate(st.session_state.analysis_results):
                                results_summary += f"\nAnalysis {i+1}: {result['task']}\n"
                                # Truncate very long results
                                if len(result['result']) > 1000:
                                    results_summary += result['result'][:1000] + "...\n"
                                else:
                                    results_summary += result['result'] + "\n"
                            
                            review_prompt = f"""
                            Problem Statement: {st.session_state.problem_statement}
                            
                            Original Analysis Guidance:
                            {st.session_state.associate_guidance}
                            
                            Analysis Results:
                            {results_summary}
                            
                            Please review these analysis results. Provide:
                            1. An assessment of how well the analyses address the problem statement
                            2. Key insights derived from the combined results
                            3. Recommendations for next steps or additional analyses
                            4. Any potential issues or limitations in the current analyses
                            """
                            
                            # Get response from Gemini API
                            associate_review = get_gemini_response(review_prompt, persona="associate")
                            
                            if associate_review:
                                add_to_conversation("associate", associate_review)
                                
                                with st.expander("Associate's Review", expanded=True):
                                    st.markdown(associate_review)
                
                if st.button("Generate Final Report"):
                    st.session_state.current_step = 5
                    st.experimental_rerun()
                    
        elif st.session_state.current_step == 5:
            # Step 6: Final Report
            st.title("📑 AI Manager - Final Report")
            
            if st.session_state.final_report is None:
                with st.spinner("AI Manager is generating the final report..."):
                    # Prepare the prompt for the Manager
                    results_summary = ""
                    for i, result in enumerate(st.session_state.analysis_results):
                        results_summary += f"\nAnalysis {i+1}: {result['task']}\n"
                        # Truncate very long results
                        if len(result['result']) > 500:
                            results_summary += result['result'][:500] + "...\n"
                        else:
                            results_summary += result['result'] + "\n"
                    
                    report_prompt = f"""
                    Project Name: {st.session_state.project_name}
                    
                    Problem Statement: {st.session_state.problem_statement}
                    
                    Original Analysis Plan:
                    {st.session_state.manager_plan}
                    
                    Data Summary:
                    {st.session_state.analyst_summary}
                    
                    Analysis Results:
                    {results_summary}
                    
                    Synthesize this information into a coherent final report for a business audience. 
                    The report should be structured with:
                    1. Executive Summary
                    2. Key Findings/Takeaways (bullet points)
                    3. Overview of Analysis Performed
                    4. Detailed Findings (referencing specific analyses)
                    5. Limitations (if any observed)
                    6. Recommendations/Next Steps (if applicable based on findings)
                    
                    Format the output in Markdown suitable for direct rendering in HTML.
                    """
                    
                    # Get response from Gemini API
                    final_report = get_gemini_response(report_prompt, persona="manager")
                    
                    if final_report:
                        st.session_state.final_report = final_report
                        add_to_conversation("manager", final_report)
            
            if st.session_state.final_report:
                st.markdown(st.session_state.final_report)
                
                # Allow user to provide feedback
                with st.expander("Provide feedback on the final report"):
                    report_feedback = st.text_area("Your feedback:", key="report_feedback")
                    if st.button("Send Feedback"):
                        if report_feedback:
                            add_to_conversation("user", f"Feedback on report: {report_feedback}")
                            
                            # Process the feedback with Gemini
                            feedback_prompt = f"""
                            Original Report: 
                            {st.session_state.final_report}
                            
                            User Feedback: 
                            {report_feedback}
                            
                            Please revise the report based on this feedback. 
                            Keep the same structured format with all the required sections.
                            """
                            
                            with st.spinner("AI Manager is revising the report..."):
                                revised_report = get_gemini_response(feedback_prompt, persona="manager")
                                if revised_report:
                                    st.session_state.final_report = revised_report
                                    add_to_conversation("manager", revised_report)
                                    st.success("Report updated based on your feedback!")
                                    st.experimental_rerun()
                
                # Download report as HTML
                if st.button("Download Report as HTML"):
                    # Convert markdown to HTML
                    import markdown
                    html_content = markdown.markdown(st.session_state.final_report)
                    
                    # Create a styled HTML document
                    styled_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>{st.session_state.project_name} - Analysis Report</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                            h1 {{ color: #2c3e50; }}
                            h2 {{ color: #3498db; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                            h3 {{ color: #2980b9; }}
                            li {{ margin-bottom: 5px; }}
                            .footer {{ margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; font-size: 0.8em; color: #7f8c8d; }}
                        </style>
                    </head>
                    <body>
                        <h1>{st.session_state.project_name} - Analysis Report</h1>
                        {html_content}
                        <div class="footer">
                            <p>Generated by AI Data Analysis Assistant</p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Save the HTML file
                    report_path = os.path.join(os.getcwd(), "report.html")
                    with open(report_path, "w") as f:
                        f.write(styled_html)
                    
                    # Provide download link
                    st.success(f"Report saved as {report_path}")
                    
                    # In a real deployment, you would provide a download link here
                    st.markdown(f"Report is ready for download at: `{report_path}`")
    
    # Display conversation history in a sidebar expander
    with st.sidebar:
        with st.expander("Conversation History"):
            for message in st.session_state.conversation_history:
                role = message["role"]
                content = message["content"]
                
                if role == "user":
                    st.markdown(f"**You:** {content}")
                elif role == "manager":
                    st.markdown(f"**AI Manager:** {content[:100]}...")
                elif role == "analyst":
                    st.markdown(f"**AI Analyst:** {content[:100]}...")
                elif role == "associate":
                    st.markdown(f"**AI Associate:** {content[:100]}...")
                
                st.markdown("---")

if __name__ == "__main__":
    main()
