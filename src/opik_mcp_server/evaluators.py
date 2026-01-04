"""
Evaluation engines for different types of agent systems using Claude 3.5 Sonnet
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import boto3
import opik
from opik import track

from .models import (
    AgentConversation,
    AgentType,
    EvaluationMetric,
    EvaluationRequest,
    EvaluationResult,
    EvaluationScore,
    MultiAgentEvaluationRequest,
    TestCase
)
from .config import settings


class LLMEvaluator:
    """Base LLM evaluator using Claude 3.5 Sonnet via Amazon Bedrock"""
    
    def __init__(self):
        # Use AWS_PROFILE from environment if set, otherwise use default
        import os
        profile = os.environ.get('AWS_PROFILE', 'default')
        session = boto3.Session(profile_name=profile, region_name=settings.aws_region)
        self.bedrock_client = session.client('bedrock-runtime')
        # Claude 3.5 Sonnet via EU inference profile
        self.model_id = "eu.anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    async def _call_claude(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call Claude 3.5 Sonnet via Bedrock"""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "top_p": 0.9
            }
            
            # Run synchronous boto3 call in executor for async compatibility
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json"
                )
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            return f"LLM evaluation failed: {str(e)}"
    
    def _parse_llm_response(self, response: str) -> Tuple[float, str]:
        """Parse LLM response to extract score and explanation"""
        try:
            lines = response.strip().split('\n')
            score = 0.5
            explanation = "Evaluation completed"
            
            for line in lines:
                line_upper = line.upper().strip()
                if line_upper.startswith('SCORE:'):
                    score_str = line.split(':', 1)[1].strip()
                    # Handle potential extra text after score
                    score_str = score_str.split()[0] if score_str else "0.5"
                    score = float(score_str)
                elif line_upper.startswith('EXPLANATION:'):
                    explanation = line.split(':', 1)[1].strip()
            
            return max(0.0, min(1.0, score)), explanation
            
        except Exception as e:
            return 0.5, f"Failed to parse evaluation: {str(e)}"


class AccuracyMetric(LLMEvaluator):
    """Accuracy evaluation metric using Claude 3.5 Sonnet"""
    
    def __init__(self):
        super().__init__()
        self.name = "accuracy"
    
    async def score(self, input_data: Dict[str, Any], output_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None) -> Tuple[float, str]:
        """Score accuracy using Claude 3.5 Sonnet"""
        input_text = input_data.get("input", "")
        output = output_data.get("output", "")
        expected = reference_data.get("expected_output", "") if reference_data else ""
        
        prompt = f"""You are an expert evaluator assessing the accuracy of AI agent responses.

Task: Evaluate how accurate and factually correct the agent's response is compared to the expected response.

Input Query: {input_text}

Agent Response: {output}

Expected Response: {expected}

Evaluation Criteria:
- Factual correctness
- Completeness of information
- Alignment with expected response
- Absence of hallucinations or errors

Please provide:
1. A score from 0.0 to 1.0 (where 1.0 is perfectly accurate)
2. A brief explanation of your scoring

Format your response EXACTLY as:
SCORE: [number between 0.0 and 1.0]
EXPLANATION: [Your reasoning in one sentence]"""

        response = await self._call_claude(prompt)
        return self._parse_llm_response(response)


class RelevanceMetric(LLMEvaluator):
    """Relevance evaluation metric using Claude 3.5 Sonnet"""
    
    def __init__(self):
        super().__init__()
        self.name = "relevance"
    
    async def score(self, input_data: Dict[str, Any], output_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None) -> Tuple[float, str]:
        """Score relevance using Claude 3.5 Sonnet"""
        input_text = input_data.get("input", "")
        output = output_data.get("output", "")
        context = input_data.get("context", {})
        
        prompt = f"""You are an expert evaluator assessing the relevance of AI agent responses.

Task: Evaluate how relevant and on-topic the agent's response is to the user's query.

User Query: {input_text}

Context: {json.dumps(context, indent=2) if context else "No additional context"}

Agent Response: {output}

Evaluation Criteria:
- Direct relevance to the user's question
- Appropriate use of context
- Staying on topic
- Addressing the core intent

Please provide:
1. A score from 0.0 to 1.0 (where 1.0 is perfectly relevant)
2. A brief explanation of your scoring

Format your response EXACTLY as:
SCORE: [number between 0.0 and 1.0]
EXPLANATION: [Your reasoning in one sentence]"""

        response = await self._call_claude(prompt)
        return self._parse_llm_response(response)


class CoherenceMetric(LLMEvaluator):
    """Coherence evaluation metric using Claude 3.5 Sonnet"""
    
    def __init__(self):
        super().__init__()
        self.name = "coherence"
    
    async def score(self, input_data: Dict[str, Any], output_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None) -> Tuple[float, str]:
        """Score coherence using Claude 3.5 Sonnet"""
        input_text = input_data.get("input", "")
        output = output_data.get("output", "")
        
        prompt = f"""You are an expert evaluator assessing the coherence of AI agent responses.

Task: Evaluate how coherent, well-structured, and logically organized the agent's response is.

User Query: {input_text}

Agent Response: {output}

Evaluation Criteria:
- Logical flow and structure
- Clear and understandable language
- Consistent reasoning throughout
- Proper grammar and syntax
- Well-organized information

Please provide:
1. A score from 0.0 to 1.0 (where 1.0 is perfectly coherent)
2. A brief explanation of your scoring

Format your response EXACTLY as:
SCORE: [number between 0.0 and 1.0]
EXPLANATION: [Your reasoning in one sentence]"""

        response = await self._call_claude(prompt)
        return self._parse_llm_response(response)


class HelpfulnessMetric(LLMEvaluator):
    """Helpfulness evaluation metric using Claude 3.5 Sonnet"""
    
    def __init__(self):
        super().__init__()
        self.name = "helpfulness"
    
    async def score(self, input_data: Dict[str, Any], output_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None) -> Tuple[float, str]:
        """Score helpfulness using Claude 3.5 Sonnet"""
        input_text = input_data.get("input", "")
        output = output_data.get("output", "")
        
        prompt = f"""You are an expert evaluator assessing the helpfulness of AI agent responses.

Task: Evaluate how helpful and actionable the agent's response is to the user.

User Query: {input_text}

Agent Response: {output}

Evaluation Criteria:
- Provides actionable information or guidance
- Addresses the user's needs effectively
- Offers clear next steps or solutions
- Demonstrates understanding of user intent
- Provides value to the user

Please provide:
1. A score from 0.0 to 1.0 (where 1.0 is extremely helpful)
2. A brief explanation of your scoring

Format your response EXACTLY as:
SCORE: [number between 0.0 and 1.0]
EXPLANATION: [Your reasoning in one sentence]"""

        response = await self._call_claude(prompt)
        return self._parse_llm_response(response)


class ConversationQualityMetric(LLMEvaluator):
    """Conversation quality metric for multi-agent scenarios using Claude 3.5 Sonnet"""
    
    def __init__(self):
        super().__init__()
        self.name = "conversation_quality"
    
    async def score(self, input_data: Dict[str, Any], output_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None) -> Tuple[float, str]:
        """Score conversation quality using Claude 3.5 Sonnet"""
        messages = input_data.get("messages", [])
        conversation = input_data.get("conversation", "")
        
        if not messages and not conversation:
            return 0.0, "No conversation data provided"
        
        # Format messages for evaluation
        if messages:
            formatted_msgs = "\n".join([
                f"{msg.get('from_agent', 'Unknown')} -> {msg.get('to_agent', 'Unknown')}: {msg.get('message', '')}"
                for msg in messages
            ])
        else:
            formatted_msgs = conversation
        
        prompt = f"""You are an expert evaluator assessing the quality of multi-agent conversations.

Task: Evaluate the overall quality of this multi-agent conversation.

Conversation:
{formatted_msgs}

Evaluation Criteria:
- Coherent flow between agents
- Clear communication and handoffs
- Productive exchanges that advance the goal
- Appropriate agent interactions
- Overall conversation effectiveness

Please provide:
1. A score from 0.0 to 1.0 (where 1.0 is excellent conversation quality)
2. A brief explanation of your scoring

Format your response EXACTLY as:
SCORE: [number between 0.0 and 1.0]
EXPLANATION: [Your reasoning in one sentence]"""

        response = await self._call_claude(prompt)
        return self._parse_llm_response(response)


class AgentCoordinationMetric(LLMEvaluator):
    """Agent coordination metric using Claude 3.5 Sonnet"""
    
    def __init__(self):
        super().__init__()
        self.name = "agent_coordination"
    
    async def score(self, input_data: Dict[str, Any], output_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None) -> Tuple[float, str]:
        """Score agent coordination using Claude 3.5 Sonnet"""
        messages = input_data.get("messages", [])
        agents = input_data.get("agents", [])
        
        if len(messages) < 2:
            return 0.5, "Insufficient messages for coordination evaluation"
        
        # Format messages for evaluation
        formatted_msgs = "\n".join([
            f"{msg.get('from_agent', 'Unknown')} -> {msg.get('to_agent', 'Unknown')}: {msg.get('message', '')}"
            for msg in messages
        ])
        
        prompt = f"""You are an expert evaluator assessing agent coordination in multi-agent systems.

Task: Evaluate how well the agents coordinate with each other.

Participating Agents: {', '.join(agents) if agents else 'Multiple agents'}

Conversation:
{formatted_msgs}

Evaluation Criteria:
- Proper handoffs between agents
- Clear role delineation
- Effective task delegation
- Minimal redundancy or confusion
- Smooth workflow transitions

Please provide:
1. A score from 0.0 to 1.0 (where 1.0 is excellent coordination)
2. A brief explanation of your scoring

Format your response EXACTLY as:
SCORE: [number between 0.0 and 1.0]
EXPLANATION: [Your reasoning in one sentence]"""

        response = await self._call_claude(prompt)
        return self._parse_llm_response(response)


class WorkflowEfficiencyMetric(LLMEvaluator):
    """Workflow efficiency metric using Claude 3.5 Sonnet"""
    
    def __init__(self):
        super().__init__()
        self.name = "workflow_efficiency"
    
    async def score(self, input_data: Dict[str, Any], output_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None) -> Tuple[float, str]:
        """Score workflow efficiency using Claude 3.5 Sonnet"""
        messages = input_data.get("messages", [])
        workflow_type = input_data.get("workflow_type", "unknown")
        
        if not messages:
            return 0.5, "No workflow data provided"
        
        # Format messages for evaluation
        formatted_msgs = "\n".join([
            f"{msg.get('from_agent', 'Unknown')} -> {msg.get('to_agent', 'Unknown')}: {msg.get('message', '')}"
            for msg in messages
        ])
        
        prompt = f"""You are an expert evaluator assessing workflow efficiency in multi-agent systems.

Task: Evaluate the efficiency of this {workflow_type} workflow.

Workflow Messages ({len(messages)} total):
{formatted_msgs}

Evaluation Criteria:
- Minimal unnecessary steps or messages
- Direct path to goal completion
- Efficient use of agent capabilities
- No redundant communications
- Optimal task distribution

Please provide:
1. A score from 0.0 to 1.0 (where 1.0 is highly efficient)
2. A brief explanation of your scoring

Format your response EXACTLY as:
SCORE: [number between 0.0 and 1.0]
EXPLANATION: [Your reasoning in one sentence]"""

        response = await self._call_claude(prompt)
        return self._parse_llm_response(response)



class OpikEvaluator:
    """Base evaluator using Opik framework with Claude 3.5 Sonnet LLM evaluation"""
    
    def __init__(self):
        self.client = opik.Opik(
            api_key=settings.opik_api_key,
            workspace=settings.opik_workspace,
            host=settings.opik_base_url
        )
        self._metric_mapping = {
            EvaluationMetric.ACCURACY: AccuracyMetric(),
            EvaluationMetric.RELEVANCE: RelevanceMetric(),
            EvaluationMetric.COHERENCE: CoherenceMetric(),
            EvaluationMetric.HELPFULNESS: HelpfulnessMetric(),
            EvaluationMetric.CONVERSATION_QUALITY: ConversationQualityMetric(),
            EvaluationMetric.AGENT_COORDINATION: AgentCoordinationMetric(),
            EvaluationMetric.WORKFLOW_EFFICIENCY: WorkflowEfficiencyMetric(),
        }
    
    def _get_metric_evaluators(self, metrics: List[EvaluationMetric]) -> List[LLMEvaluator]:
        """Convert evaluation metrics to metric evaluator objects"""
        evaluators = []
        for metric in metrics:
            if metric in self._metric_mapping:
                evaluators.append(self._metric_mapping[metric])
            else:
                # Default to accuracy metric for unknown metrics
                evaluators.append(AccuracyMetric())
        return evaluators
    
    def _log_trace_to_opik(self, evaluation_id: str, input_data: dict, output_data: dict, 
                           scores: list, project_name: str) -> str:
        """Explicitly log trace to Opik platform"""
        try:
            # Create trace in Opik
            trace = self.client.trace(
                name=f"evaluation-{evaluation_id}",
                project_name=project_name,
                input=input_data,
                output=output_data,
                metadata={
                    "evaluation_id": evaluation_id,
                    "scores": [{"metric": s.metric.value, "score": s.score, "explanation": s.explanation} for s in scores],
                    "model": "eu.anthropic.claude-3-5-sonnet-20240620-v1:0",
                    "evaluator": "OpikMCPServer"
                }
            )
            return trace.id if hasattr(trace, 'id') else evaluation_id
        except Exception as e:
            # Log error but don't fail evaluation
            import logging
            logging.getLogger(__name__).warning(f"Failed to log trace to Opik: {e}")
            return evaluation_id
    
    @track(project_name="opik-mcp-evaluations")
    async def evaluate_single_case(
        self,
        test_case: TestCase,
        agent_response: str,
        metrics: List[EvaluationMetric],
        project_name: str = "default"
    ) -> EvaluationResult:
        """Evaluate a single test case using Claude 3.5 Sonnet"""
        start_time = time.time()
        evaluation_id = str(uuid.uuid4())
        
        # Prepare evaluation data
        input_data = {
            "input": test_case.input,
            "context": test_case.context
        }
        
        output_data = {
            "output": agent_response
        }
        
        reference_data = {
            "expected_output": test_case.expected_output
        }
        
        # Get metric evaluators
        metric_evaluators = self._get_metric_evaluators(metrics)
        
        # Run evaluation with LLM
        scores = []
        for i, metric in enumerate(metrics):
            try:
                if i < len(metric_evaluators):
                    evaluator = metric_evaluators[i]
                    # Call async LLM evaluation
                    score_value, explanation = await evaluator.score(input_data, output_data, reference_data)
                    
                    score = EvaluationScore(
                        metric=metric,
                        score=score_value,
                        explanation=explanation,
                        passed=score_value >= 0.7,
                        threshold=0.7
                    )
                    scores.append(score)
                
            except Exception as e:
                # Fallback score on error
                score = EvaluationScore(
                    metric=metric,
                    score=0.0,
                    explanation=f"Evaluation failed: {str(e)}",
                    passed=False,
                    threshold=0.7
                )
                scores.append(score)
        
        # Calculate overall score
        overall_score = sum(s.score for s in scores) / len(scores) if scores else 0.0
        passed = overall_score >= 0.7
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log trace to Opik explicitly
        opik_trace_id = self._log_trace_to_opik(
            evaluation_id=evaluation_id,
            input_data=input_data,
            output_data={"output": agent_response, "scores": [s.dict() for s in scores]},
            scores=scores,
            project_name=project_name
        )
        
        return EvaluationResult(
            evaluation_id=evaluation_id,
            test_case_id=test_case.id,
            scores=scores,
            overall_score=overall_score,
            passed=passed,
            execution_time_ms=execution_time,
            session_id=test_case.session_id,
            opik_trace_id=opik_trace_id,
            metadata=test_case.metadata
        )


class AgentEvaluator(OpikEvaluator):
    """Evaluator for AI agents with Claude 3.5 Sonnet LLM evaluation"""
    
    @track(project_name="opik-mcp-evaluations")
    async def evaluate_agent(
        self,
        request: EvaluationRequest,
        agent_function: callable
    ) -> List[EvaluationResult]:
        """Evaluate an AI agent with multiple test cases"""
        results = []
        
        # Create Opik experiment
        experiment_name = request.experiment_name or f"agent-eval-{request.agent_id}-{int(time.time())}"
        
        for test_case in request.test_cases:
            try:
                # Execute agent function
                agent_response = await self._execute_agent_safely(
                    agent_function, 
                    test_case.input,
                    test_case.context
                )
                
                # Evaluate response with LLM
                result = await self.evaluate_single_case(
                    test_case=test_case,
                    agent_response=agent_response,
                    metrics=request.evaluators,
                    project_name=request.project_name
                )
                
                result.agent_id = request.agent_id
                results.append(result)
                
            except Exception as e:
                # Create failed result
                result = EvaluationResult(
                    evaluation_id=str(uuid.uuid4()),
                    agent_id=request.agent_id,
                    test_case_id=test_case.id,
                    scores=[],
                    overall_score=0.0,
                    passed=False,
                    execution_time_ms=0.0,
                    session_id=test_case.session_id,
                    metadata={"error": str(e)}
                )
                results.append(result)
        
        return results
    
    async def _execute_agent_safely(
        self,
        agent_function: callable,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute agent function safely with timeout"""
        try:
            # Execute with timeout
            response = await asyncio.wait_for(
                agent_function(input_text, context or {}),
                timeout=settings.evaluation_timeout
            )
            return str(response)
        except asyncio.TimeoutError:
            return "Agent execution timed out"
        except Exception as e:
            return f"Agent execution failed: {str(e)}"


class MultiAgentEvaluator(OpikEvaluator):
    """Evaluator for multi-agent systems and workflows with Claude 3.5 Sonnet LLM evaluation"""
    
    @track(project_name="opik-mcp-evaluations")
    async def evaluate_multiagent_workflow(
        self,
        request: MultiAgentEvaluationRequest,
        workflow_function: Optional[callable] = None
    ) -> EvaluationResult:
        """Evaluate a multi-agent workflow using LLM"""
        start_time = time.time()
        evaluation_id = str(uuid.uuid4())
        
        conversation = request.conversation
        
        # Prepare evaluation data for multi-agent context
        input_data = {
            "workflow_type": request.workflow_type.value,
            "agents": conversation.agents,
            "messages": [msg.dict() for msg in conversation.messages],
            "conversation": self._format_conversation(conversation),
            "start_time": str(conversation.messages[0].timestamp) if conversation.messages else str(datetime.utcnow()),
            "end_time": str(conversation.messages[-1].timestamp) if conversation.messages else str(datetime.utcnow()),
        }
        
        output_data = {
            "workflow_result": "Multi-agent workflow completed"
        }
        
        # Get specialized metrics for multi-agent evaluation
        metric_evaluators = self._get_metric_evaluators(request.evaluators)
        
        # Run LLM evaluations
        scores = []
        for i, metric in enumerate(request.evaluators):
            try:
                if i < len(metric_evaluators):
                    evaluator = metric_evaluators[i]
                    # Call async LLM evaluation
                    score_value, explanation = await evaluator.score(input_data, output_data)
                    
                    score = EvaluationScore(
                        metric=metric,
                        score=score_value,
                        explanation=explanation,
                        passed=score_value >= 0.7,
                        threshold=0.7
                    )
                    scores.append(score)
                    
            except Exception as e:
                score = EvaluationScore(
                    metric=metric,
                    score=0.0,
                    explanation=f"Multi-agent evaluation failed: {str(e)}",
                    passed=False,
                    threshold=0.7
                )
                scores.append(score)
        
        # Calculate overall score
        overall_score = sum(s.score for s in scores) / len(scores) if scores else 0.0
        passed = overall_score >= 0.7
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log trace to Opik explicitly
        opik_trace_id = self._log_trace_to_opik(
            evaluation_id=evaluation_id,
            input_data=input_data,
            output_data={"workflow_result": "completed", "scores": [s.dict() for s in scores]},
            scores=scores,
            project_name=request.project_name
        )
        
        return EvaluationResult(
            evaluation_id=evaluation_id,
            workflow_id=request.workflow_id,
            scores=scores,
            overall_score=overall_score,
            passed=passed,
            execution_time_ms=execution_time,
            opik_trace_id=opik_trace_id,
            metadata={
                "workflow_type": request.workflow_type.value,
                "agent_count": len(conversation.agents),
                "message_count": len(conversation.messages)
            }
        )
    
    def _format_conversation(self, conversation: AgentConversation) -> str:
        """Format conversation for evaluation"""
        formatted = []
        for msg in conversation.messages:
            formatted.append(f"{msg.from_agent} -> {msg.to_agent}: {msg.message}")
        return "\n".join(formatted)
    
    async def evaluate_agent2agent_flow(
        self,
        request: MultiAgentEvaluationRequest
    ) -> EvaluationResult:
        """Specialized evaluation for Agent2Agent (A2A) workflows"""
        # Add A2A specific evaluation logic
        result = await self.evaluate_multiagent_workflow(request)
        
        # Add A2A specific metrics using LLM
        a2a_score, a2a_explanation = await self._evaluate_a2a_protocol_compliance_llm(request.conversation)
        
        a2a_eval_score = EvaluationScore(
            metric=EvaluationMetric.AGENT_COORDINATION,
            score=a2a_score,
            explanation=a2a_explanation,
            passed=a2a_score >= 0.7,
            threshold=0.7
        )
        
        result.scores.append(a2a_eval_score)
        result.overall_score = sum(s.score for s in result.scores) / len(result.scores)
        result.passed = result.overall_score >= 0.7
        
        return result
    
    async def _evaluate_a2a_protocol_compliance_llm(self, conversation: AgentConversation) -> Tuple[float, str]:
        """Evaluate A2A protocol compliance using Claude 3.5 Sonnet"""
        if not conversation.messages:
            return 0.0, "No messages in conversation"
        
        # Format conversation for LLM evaluation
        formatted_msgs = "\n".join([
            f"{msg.from_agent} -> {msg.to_agent}: {msg.message}"
            for msg in conversation.messages
        ])
        
        evaluator = LLMEvaluator()
        prompt = f"""You are an expert evaluator assessing Agent2Agent (A2A) protocol compliance.

Task: Evaluate how well this multi-agent conversation follows A2A protocol standards.

Conversation:
{formatted_msgs}

Evaluation Criteria:
- Proper message routing between agents
- Clear sender and receiver identification
- Appropriate handoff protocols
- Message format consistency
- Protocol adherence

Please provide:
1. A score from 0.0 to 1.0 (where 1.0 is fully compliant)
2. A brief explanation of your scoring

Format your response EXACTLY as:
SCORE: [number between 0.0 and 1.0]
EXPLANATION: [Your reasoning in one sentence]"""

        response = await evaluator._call_claude(prompt)
        return evaluator._parse_llm_response(response)
