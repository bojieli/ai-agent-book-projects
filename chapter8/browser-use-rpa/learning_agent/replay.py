"""
Workflow replay functionality using Playwright.

This module provides reliable replay of learned workflows by directly
controlling the browser through Playwright, bypassing the need for LLM calls.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from playwright.async_api import Page, Browser, async_playwright, Locator
import time

from .workflow import Workflow, WorkflowStep, ActionType, StatePredicate, PredicateType


logger = logging.getLogger(__name__)


class PredicateFailure(RuntimeError):
    """Raised when the real page no longer satisfies a workflow assertion."""


class WorkflowReplayer:
    """
    Replays learned workflows using Playwright for direct browser control.
    
    This replayer:
    - Executes workflows without LLM calls
    - Handles dynamic page loading with smart waits
    - Provides robust error recovery
    - Tracks execution metrics
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize the workflow replayer.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None
        self.playwright = None
    
    async def setup(self):
        """Initialize Playwright and browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(30000)
        
        logger.info("Workflow replayer initialized")
    
    async def cleanup(self):
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def replay_workflow(self, 
                             workflow: Workflow, 
                             parameters: Optional[Dict[str, Any]] = None,
                             initial_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Replay a workflow with the given parameters.
        
        Args:
            workflow: The workflow to replay
            parameters: Parameters to apply to the workflow
            initial_url: Starting URL (uses workflow's initial_url if not provided)
        
        Returns:
            Dictionary containing execution results and metrics
        """
        start_time = time.time()
        results = {
            "success": False,
            "steps_completed": 0,
            "total_steps": len(workflow.steps),
            "errors": [],
            "execution_time": 0,
            "model_calls_saved": len(workflow.steps),  # Each step would require an LLM call
            "failed_predicate": None,
            "fallback_required": False,
        }
        
        try:
            # Apply parameters if provided
            if parameters:
                workflow = workflow.parameterize(parameters)
            
            # Navigate to initial URL
            start_url = initial_url or workflow.initial_url
            if start_url:
                logger.info(f"Navigating to initial URL: {start_url}")
                await self.page.goto(start_url, wait_until='domcontentloaded')
                await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Execute each step
            for i, step in enumerate(workflow.steps):
                logger.info(f"Executing step {i+1}/{len(workflow.steps)}: {step.action_type.value}")
                
                try:
                    await self._check_predicates(step.preconditions, f"step {i+1} precondition")
                    await self._execute_step(step)
                    await self._check_predicates(step.postconditions, f"step {i+1} postcondition")
                    results["steps_completed"] += 1
                    
                    # Small delay between actions for stability
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    error_msg = f"Step {i+1} failed: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    
                    if isinstance(e, PredicateFailure):
                        results["failed_predicate"] = str(e)
                    # A state mismatch makes all later actions unsafe. Stop
                    # instead of claiming partial action execution as success.
                    break
            
            if results["steps_completed"] == results["total_steps"]:
                await self._check_predicates(workflow.final_predicates, "workflow final predicate")
                results["success"] = True
            
        except Exception as e:
            logger.error(f"Workflow replay failed: {e}")
            results["errors"].append(str(e))
            if isinstance(e, PredicateFailure):
                results["failed_predicate"] = str(e)
        
        finally:
            results["execution_time"] = time.time() - start_time
            results["fallback_required"] = not results["success"]
            logger.info(f"Workflow replay completed in {results['execution_time']:.2f}s")
        
        return results

    async def _check_predicates(self, predicates, location: str) -> None:
        for predicate in predicates:
            ok, actual = await self._evaluate_predicate(predicate)
            if not ok:
                description = predicate.description or predicate.predicate_type.value
                raise PredicateFailure(
                    f"{location} failed: {description}; expected={predicate.expected!r}, actual={actual!r}"
                )

    async def _evaluate_predicate(self, predicate: StatePredicate):
        if self.page is None:
            return False, "page is not initialized"
        if predicate.predicate_type == PredicateType.URL_CONTAINS:
            actual = self.page.url
            return str(predicate.expected) in actual, actual
        if predicate.predicate_type == PredicateType.ELEMENT_VISIBLE:
            if not predicate.selector:
                return False, "missing selector"
            locator = self.page.locator(predicate.selector)
            actual = await locator.count() > 0 and await locator.first.is_visible()
            return actual == bool(predicate.expected), actual
        if predicate.predicate_type == PredicateType.ELEMENT_TEXT_CONTAINS:
            if not predicate.selector:
                return False, "missing selector"
            locator = self.page.locator(predicate.selector).first
            if await locator.count() == 0:
                return False, "element missing"
            actual = await locator.inner_text()
            return str(predicate.expected) in actual, actual
        if predicate.predicate_type == PredicateType.PAGE_STATE_EQUALS:
            if not predicate.state_key:
                return False, "missing state_key"
            actual = await self.page.evaluate(
                "key => window.__agentState ? window.__agentState[key] : undefined",
                predicate.state_key,
            )
            return actual == predicate.expected, actual
        return False, f"unsupported predicate {predicate.predicate_type}"
    
    async def _execute_step(self, step: WorkflowStep) -> None:
        """
        Execute a single workflow step.
        
        Args:
            step: The step to execute
        """
        # Wait before action if specified
        if step.wait_before > 0:
            await asyncio.sleep(step.wait_before)
        
        # Execute based on action type
        if step.action_type == ActionType.NAVIGATE:
            await self._execute_navigate(step)
        elif step.action_type == ActionType.CLICK:
            await self._execute_click(step)
        elif step.action_type == ActionType.INPUT_TEXT:
            await self._execute_input(step)
        elif step.action_type == ActionType.SELECT_OPTION:
            await self._execute_select(step)
        elif step.action_type == ActionType.SCROLL:
            await self._execute_scroll(step)
        elif step.action_type == ActionType.WAIT:
            await self._execute_wait(step)
        elif step.action_type == ActionType.SWITCH_TAB:
            await self._execute_switch_tab(step)
        elif step.action_type == ActionType.UPLOAD_FILE:
            await self._execute_upload(step)
        else:
            logger.warning(f"Unsupported action type: {step.action_type}")
    
    async def _get_element(self, step: WorkflowStep) -> Locator:
        """
        Get element using stable selectors with fallback.
        
        Args:
            step: The step containing selector information
        
        Returns:
            Playwright Locator for the element
        """
        locator = None
        
        # Try XPath first (most stable)
        if step.xpath:
            try:
                locator = self.page.locator(f"xpath={step.xpath}")
                # Check if element exists
                if await locator.count() > 0:
                    # Wait for element to be ready
                    await locator.wait_for(state='visible', timeout=step.timeout * 1000)
                    return locator
            except Exception as e:
                logger.debug(f"XPath locator failed: {e}")
        
        # Try CSS selector as fallback
        if step.css_selector:
            try:
                locator = self.page.locator(step.css_selector)
                if await locator.count() > 0:
                    await locator.wait_for(state='visible', timeout=step.timeout * 1000)
                    return locator
            except Exception as e:
                logger.debug(f"CSS selector failed: {e}")
        
        # Try to build selector from attributes
        if step.element_attributes:
            selector_parts = []
            
            # Use ID if available
            if 'id' in step.element_attributes:
                return self.page.locator(f"#{step.element_attributes['id']}")
            
            # Build attribute selector
            for attr, value in step.element_attributes.items():
                if attr in ['name', 'type', 'role', 'aria-label', 'data-testid']:
                    selector_parts.append(f"[{attr}='{value}']")
            
            if selector_parts:
                selector = ''.join(selector_parts)
                try:
                    locator = self.page.locator(selector)
                    if await locator.count() > 0:
                        await locator.wait_for(state='visible', timeout=step.timeout * 1000)
                        return locator
                except Exception as e:
                    logger.debug(f"Attribute selector failed: {e}")
        
        # Try text content as last resort
        if 'text' in step.parameters:
            text = step.parameters['text']
            locator = self.page.get_by_text(text)
            if await locator.count() > 0:
                return locator
        
        raise Exception(f"Could not find element for step: {step.description or step.action_type}")
    
    async def _execute_navigate(self, step: WorkflowStep) -> None:
        """Execute navigation action."""
        url = step.parameters.get('url')
        if url:
            logger.debug(f"Navigating to: {url}")
            await self.page.goto(url, wait_until='domcontentloaded')
            await self.page.wait_for_load_state('networkidle', timeout=10000)
    
    async def _execute_click(self, step: WorkflowStep) -> None:
        """Execute click action with smart waiting."""
        element = await self._get_element(step)
        
        # Ensure element is clickable
        await element.wait_for(state='visible', timeout=step.timeout * 1000)
        await element.scroll_into_view_if_needed()
        
        # Check for ctrl/cmd modifier
        if step.parameters.get('while_holding_ctrl'):
            await element.click(modifiers=['Control'])
        else:
            await element.click()
        
        # Wait for potential navigation or dynamic updates
        try:
            await self.page.wait_for_load_state('networkidle', timeout=5000)
        except:
            pass  # Page might not navigate
    
    async def _execute_input(self, step: WorkflowStep) -> None:
        """Execute text input action."""
        element = await self._get_element(step)
        text = step.parameters.get('text', '')
        clear_existing = step.parameters.get('clear_existing', True)
        
        # Click to focus
        await element.click()
        
        # Clear existing text if needed
        if clear_existing:
            await element.fill('')
        
        # Type the text
        await element.type(text, delay=50)  # Small delay for more human-like typing
    
    async def _execute_select(self, step: WorkflowStep) -> None:
        """Execute select option action."""
        element = await self._get_element(step)
        option_text = step.parameters.get('text', '')
        
        # Try to select by visible text
        await element.select_option(label=option_text)
    
    async def _execute_scroll(self, step: WorkflowStep) -> None:
        """Execute scroll action."""
        direction = 'down' if step.parameters.get('down', True) else 'up'
        pages = step.parameters.get('num_pages', 1)
        
        # Calculate scroll amount
        viewport_height = await self.page.evaluate('window.innerHeight')
        scroll_amount = viewport_height * pages
        
        if direction == 'down':
            await self.page.evaluate(f'window.scrollBy(0, {scroll_amount})')
        else:
            await self.page.evaluate(f'window.scrollBy(0, -{scroll_amount})')
        
        # Wait for any lazy-loaded content
        await asyncio.sleep(0.5)
    
    async def _execute_wait(self, step: WorkflowStep) -> None:
        """Execute wait action."""
        wait_time = step.parameters.get('seconds', 1)
        await asyncio.sleep(wait_time)
    
    async def _execute_switch_tab(self, step: WorkflowStep) -> None:
        """Execute tab switching (simplified for single tab replay)."""
        # In replay mode, we typically work with a single tab
        # This is a placeholder for multi-tab support
        logger.debug("Tab switching in replay mode - continuing in current tab")
    
    async def _execute_upload(self, step: WorkflowStep) -> None:
        """Execute file upload action."""
        element = await self._get_element(step)
        file_path = step.parameters.get('path', '')
        
        # Set the file(s) to upload
        await element.set_input_files(file_path)
