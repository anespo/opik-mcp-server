#!/usr/bin/env python3
"""
Generate architecture diagram for Opik MCP Server
"""

import os
from pathlib import Path

def generate_diagram():
    """Generate the architecture diagram"""
    print("🎨 Generating Opik MCP Server architecture diagram...")
    
    # Create diagrams directory if it doesn't exist
    diagrams_dir = Path(__file__).parent.parent / "diagrams"
    diagrams_dir.mkdir(exist_ok=True)
    
    # Change to diagrams directory
    original_cwd = os.getcwd()
    os.chdir(diagrams_dir)
    
    try:
        # Architecture diagram code using AWS diagrams
        from diagrams import Diagram, Cluster, Edge
        from diagrams.aws.compute import Lambda
        from diagrams.aws.management import Cloudwatch
        from diagrams.aws.devtools import XRay
        from diagrams.aws.ml import Bedrock
        from diagrams.aws.storage import S3
        from diagrams.aws.network import APIGateway
        from diagrams.aws.integration import SQS
        from diagrams.onprem.client import Users
        from diagrams.onprem.compute import Server
        from diagrams.programming.framework import FastAPI
        from diagrams.programming.language import Python

        with Diagram("Opik MCP Server Architecture on AWS AgentCore", show=False, direction="TB"):
            
            # Users and clients
            users = Users("Developers\\n& AI Engineers")
            kiro = Server("Kiro IDE\\n(MCP Client)")
            
            with Cluster("AWS Bedrock AgentCore"):
                with Cluster("Opik MCP Server Runtime"):
                    mcp_server = FastAPI("FastMCP Server\\n(Opik Evaluation)")
                    lambda_runtime = Lambda("AgentCore Runtime\\n(Python 3.11)")
                    
                with Cluster("Observability & Monitoring"):
                    cloudwatch = Cloudwatch("CloudWatch\\nLogs & Metrics")
                    xray = XRay("X-Ray\\nTracing")
                    dashboard = Cloudwatch("GenAI Observability\\nDashboard")
                    
                with Cluster("AI/ML Services"):
                    bedrock_models = Bedrock("Bedrock Models\\n(Claude 3.5, Nova)")
                    
            with Cluster("Opik Platform"):
                opik_api = Server("Opik API\\n(Evaluation Framework)")
                opik_dashboard = Server("Opik Dashboard\\n(Results & Analytics)")
                
            with Cluster("Strands Agents Ecosystem"):
                single_agent = Python("Single Agent\\nEvaluation")
                multiagent = Python("Multi-Agent\\nWorkflows")
                a2a = Python("Agent2Agent\\n(A2A Protocol)")
                graph_workflow = Python("Graph\\nWorkflows")
                swarm = Python("Swarm\\nIntelligence")
                
            # Main flow
            users >> kiro >> Edge(label="MCP Protocol") >> mcp_server
            mcp_server >> lambda_runtime
            
            # Evaluation flows
            mcp_server >> Edge(label="Evaluate") >> single_agent
            mcp_server >> Edge(label="Evaluate") >> multiagent
            mcp_server >> Edge(label="Evaluate") >> a2a
            mcp_server >> Edge(label="Evaluate") >> graph_workflow
            mcp_server >> Edge(label="Evaluate") >> swarm
            
            # Opik integration
            mcp_server >> Edge(label="Send Results") >> opik_api
            opik_api >> opik_dashboard
            
            # AI model integration
            mcp_server >> Edge(label="LLM Evaluation") >> bedrock_models
            
            # Observability
            lambda_runtime >> Edge(label="Logs") >> cloudwatch
            lambda_runtime >> Edge(label="Traces") >> xray
            cloudwatch >> dashboard
            xray >> dashboard
            
            # Results flow back
            opik_dashboard >> Edge(label="Analytics", style="dashed") >> users
            dashboard >> Edge(label="Monitoring", style="dashed") >> users
        
        print("✅ Architecture diagram generated successfully!")
        print(f"📁 Saved to: {diagrams_dir}/opik_mcp_server_architecture_on_aws_agentcore.png")
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install with: uv add diagrams")
        return False
    except Exception as e:
        print(f"❌ Error generating diagram: {e}")
        return False
    finally:
        os.chdir(original_cwd)
    
    return True

def generate_detailed_flow_diagram():
    """Generate detailed evaluation flow diagram"""
    print("🔄 Generating detailed evaluation flow diagram...")
    
    diagrams_dir = Path(__file__).parent.parent / "diagrams"
    original_cwd = os.getcwd()
    os.chdir(diagrams_dir)
    
    try:
        from diagrams import Diagram, Cluster, Edge
        from diagrams.aws.compute import Lambda
        from diagrams.aws.management import Cloudwatch
        from diagrams.aws.ml import Bedrock
        from diagrams.onprem.client import Users
        from diagrams.programming.framework import FastAPI
        from diagrams.programming.language import Python

        with Diagram("Opik MCP Server - Evaluation Flow", show=False, direction="LR"):
            
            user = Users("User")
            
            with Cluster("Kiro IDE"):
                kiro_chat = FastAPI("Chat Interface")
                mcp_client = Python("MCP Client")
                
            with Cluster("Opik MCP Server"):
                with Cluster("MCP Tools"):
                    eval_agent = Python("evaluate_agent")
                    eval_multiagent = Python("evaluate_multiagent_workflow")
                    batch_eval = Python("batch_evaluate_agents")
                    
                with Cluster("Evaluators"):
                    strands_eval = Python("StrandsAgentEvaluator")
                    multiagent_eval = Python("MultiAgentEvaluator")
                    opik_eval = Python("OpikEvaluator")
                    
                with Cluster("Metrics"):
                    accuracy = Python("Accuracy")
                    relevance = Python("Relevance")
                    coordination = Python("Agent Coordination")
                    workflow_eff = Python("Workflow Efficiency")
                    
            with Cluster("External Services"):
                opik_api = FastAPI("Opik API")
                bedrock = Bedrock("Bedrock Models")
                cloudwatch = Cloudwatch("CloudWatch")
                
            # User interaction flow
            user >> kiro_chat >> mcp_client
            
            # MCP tool selection
            mcp_client >> Edge(label="Single Agent") >> eval_agent
            mcp_client >> Edge(label="Multi-Agent") >> eval_multiagent
            mcp_client >> Edge(label="Batch") >> batch_eval
            
            # Evaluator routing
            eval_agent >> strands_eval
            eval_multiagent >> multiagent_eval
            batch_eval >> strands_eval
            batch_eval >> multiagent_eval
            
            # Base evaluation
            strands_eval >> opik_eval
            multiagent_eval >> opik_eval
            
            # Metrics application
            opik_eval >> accuracy
            opik_eval >> relevance
            opik_eval >> coordination
            opik_eval >> workflow_eff
            
            # External integrations
            opik_eval >> Edge(label="Log Results") >> opik_api
            opik_eval >> Edge(label="LLM Evaluation") >> bedrock
            opik_eval >> Edge(label="Observability") >> cloudwatch
            
            # Results back to user
            opik_api >> Edge(label="Results", style="dashed") >> mcp_client
            cloudwatch >> Edge(label="Metrics", style="dashed") >> mcp_client
            mcp_client >> Edge(label="Display", style="dashed") >> kiro_chat
        
        print("✅ Evaluation flow diagram generated successfully!")
        print(f"📁 Saved to: {diagrams_dir}/opik_mcp_server_evaluation_flow.png")
        return True
    except Exception as e:
        print(f"❌ Error generating flow diagram: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def main():
    """Generate all diagrams"""
    print("🏗️  Generating architecture diagrams for Opik MCP Server...")
    print("=" * 60)
    
    success = True
    
    # Generate main architecture diagram
    if not generate_diagram():
        success = False
    
    print()
    
    # Generate detailed flow diagram
    if not generate_detailed_flow_diagram():
        success = False
    
    print()
    print("=" * 60)
    
    if success:
        print("🎉 All diagrams generated successfully!")
        print()
        print("📊 Generated diagrams:")
        print("   1. opik_mcp_server_architecture_on_aws_agentcore.png - Main architecture")
        print("   2. opik_mcp_server_evaluation_flow.png - Detailed evaluation flow")
        print()
        print("💡 Use these diagrams in your AWS blog post and documentation!")
    else:
        print("❌ Some diagrams failed to generate. Check the error messages above.")
        print("💡 Make sure you have 'diagrams' package installed: uv add diagrams")

if __name__ == "__main__":
    main()