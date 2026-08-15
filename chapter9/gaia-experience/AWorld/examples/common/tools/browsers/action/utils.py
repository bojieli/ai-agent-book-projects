# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import re
import time
import traceback
from typing import Optional

from examples.common.tools.browsers.util.dom import DOMElementNode
from aworld.logs.util import logger
from aworld.utils import import_package


class DomUtil:
    def __init__(self):
        import_package("playwright")

    @staticmethod
    async def async_click_element(page, element_node: DOMElementNode, **kwargs) -> Optional[str]:
        from playwright.async_api import ElementHandle as AElementHandle, BrowserContext as ABrowserContext

        try:
            element_handle: AElementHandle = await DomUtil.async_get_locate_element(page, element_node)
            if element_handle is None:
                raise Exception(f'Element: {repr(element_node)} not found')

            bound = await element_handle.bounding_box()
            try:
                # todo: iframe.
                center_x = bound['x'] + bound['width'] / 2
                center_y = bound['y'] + bound['height'] / 2

                try:
                    browser: ABrowserContext = kwargs.get('browser')
                    async with browser.expect_page() as new_page_info:
                        await page.mouse.click(center_x, center_y)
                    await page.mouse.click(center_x, center_y)
                    await page.wait_for_load_state()
                except:
                    logger.warning(traceback.format_exc())
            except:
                logger.info(f"click {element_handle}!!")
                if await element_handle.text_content():
                    browser: ABrowserContext = kwargs.get('browser')
                    if browser:
                        try:
                            async with browser.expect_page() as new_page_info:
                                await page.click(f"text={element_handle.text_content()}")
                            page = await new_page_info.value
                            await page.wait_for_load_state()
                        except:
                            logger.warning(traceback.format_exc())
                    else:
                        await element_handle.click()
                        await page.wait_for_load_state()
                else:
                    await element_handle.click()
                    await page.wait_for_load_state()
        except Exception as e:
            logger.error(traceback.format_exc())
            raise Exception(f'Failed to click element: {repr(element_node)}. Error: {str(e)}')

    @staticmethod
    def click_element(page, element_node: DOMElementNode, **kwargs) -> Optional[str]:
        from playwright.sync_api import ElementHandle, BrowserContext

        try:
            element_handle: ElementHandle = DomUtil.get_locate_element(page, element_node)
            if element_handle is None:
                raise Exception(f'Element: {repr(element_node)} not found')

            bound = element_handle.bounding_box()
            try:
                # todo: iframe.
                center_x = bound['x'] + bound['width'] / 2
                center_y = bound['y'] + bound['height'] / 2

                try:
                    browser: BrowserContext = kwargs.get('browser')
                    with browser.expect_page() as new_page_info:
                        page.mouse.click(center_x, center_y)
                    page = new_page_info.value
                    page.wait_for_load_state()
                except:
                    logger.warning(traceback.format_exc())
            except:
                logger.info(f"click {element_handle}!!")
                if element_handle.text_content():
                    browser: BrowserContext = kwargs.get('browser')
                    if browser:
                        try:
                            with browser.expect_page() as new_page_info:
                                page.click(f"text={element_handle.text_content()}")
                            page = new_page_info.value
                            page.wait_for_load_state()
                        except:
                            logger.warning(traceback.format_exc())
                    else:
                        element_handle.click()
                        page.wait_for_load_state()
                else:
                    element_handle.click()
                    page.wait_for_load_state()
        except Exception as e:
            logger.error(traceback.format_exc())
            raise Exception(f'Failed to click element: {repr(element_node)}. Error: {str(e)}')

    @staticmethod
    async def async_get_locate_element(current_frame, element: DOMElementNode):
        # Start with the target element and collect all parents, return Optional[AElementHandle]
        from playwright.async_api import FrameLocator as AFrameLocator

        parents: list[DOMElementNode] = []
        current = element
        while current.parent is not None:
            parent = current.parent
            parents.append(parent)
            current = parent

        # Reverse the parents list to process from top to bottom
        parents.reverse()

        # Process all iframe parents in sequence
        iframes = [item for item in parents if item.tag_name == 'iframe']
        for parent in iframes:
            css_selector = DomUtil._enhanced_css_selector_for_element(
                parent,
                include_dynamic_attributes=True,
            )
            current_frame = current_frame.frame_locator(css_selector)

        css_selector = DomUtil._enhanced_css_selector_for_element(
            element, include_dynamic_attributes=True
        )

        try:
            if isinstance(current_frame, AFrameLocator):
                element_handle = await current_frame.locator(css_selector).element_handle()
                return element_handle
            else:
                # Try to scroll into view if hidden
                element_handle = await current_frame.query_selector(css_selector)
                if element_handle:
                    await element_handle.scroll_into_view_if_needed()
                    return element_handle
                return None
        except Exception as e:
            logger.error(f'Failed to locate element: {str(e)}')
            return None

    @staticmethod
    def get_locate_element(current_frame, element: DOMElementNode):
        # Start with the target element and collect all parents
        from playwright.sync_api import FrameLocator

        parents: list[DOMElementNode] = []
        current = element
        while current.parent is not None:
            parent = current.parent
            parents.append(parent)
            current = parent

        # Reverse the parents list to process from top to bottom
        parents.reverse()

        # Process all iframe parents in sequence
        iframes = [item for item in parents if item.tag_name == 'iframe']
        for parent in iframes:
            css_selector = DomUtil._enhanced_css_selector_for_element(
                parent,
                include_dynamic_attributes=True,
            )
            current_frame = current_frame.frame_locator(css_selector)

        css_selector = DomUtil._enhanced_css_selector_for_element(
            element, include_dynamic_attributes=True
        )

        try:
            if isinstance(current_frame, FrameLocator):
                element_handle = current_frame.locator(css_selector).element_handle()
                return element_handle
            else:
                # Try to scroll into view if hidden
                element_handle = current_frame.query_selector(css_selector)
                if element_handle:
                    element_handle.scroll_into_view_if_needed()
                    return element_handle
                return None
        except Exception as e:
            logger.error(f'Failed to locate element: {str(e)}')
            return None

    @staticmethod
    def wait_for_stable_network(page, **kwargs):
        pending_requests = set()
        last_activity = time.time()

        # Define relevant resource types and content types
        RELEVANT_RESOURCE_TYPES = {
            'document',
            'stylesheet',
            'image',
            'font',
            'script',
            'iframe',
        }

        RELEVANT_CONTENT_TYPES = {
            'text/html',
            'text/css',
            'application/javascript',
            'image/',
            'font/',
            'application/json',
        }

        # Additional patterns to filter out
        IGNORED_URL_PATTERNS = {
            # Analytics and tracking
            'analytics',
            'tracking',
            'telemetry',
            'beacon',
            'metrics',
            # Ad-related
            'doubleclick',
            'adsystem',
            'adserver',
            'advertising',
            # Social media widgets
            'facebook.com/plugins',
            'platform.twitter',
            'linkedin.com/embed',
            # Live chat and support
            'livechat',
            'zendesk',
            'intercom',
            'crisp.chat',
            'hotjar',
            # Push notifications
            'push-notifications',
            'onesignal',
            'pushwoosh',
            # Background sync/heartbeat
            'heartbeat',
            'ping',
            'alive',
            # WebRTC and streaming
            'webrtc',
            'rtmp://',
            'wss://',
            # Common CDNs for dynamic content
            'cloudfront.net',
            'fastly.net',
        }

        def on_request(request):
            # Filter by resource type
            if request.resource_type not in RELEVANT_RESOURCE_TYPES:
                return

            # Filter out streaming, websocket, and other real-time requests
            if request.resource_type in {
                'websocket',
                'media',
                'eventsource',
                'manifest',
                'other',
            }:
                return

            # Filter out by URL patterns
            url = request.url.lower()
            if any(pattern in url for pattern in IGNORED_URL_PATTERNS):
                return

            # Filter out data URLs and blob URLs
            if url.startswith(('data:', 'blob:')):
                return

            # Filter out requests with certain headers
            headers = request.headers
            if headers.get('purpose') == 'prefetch' or headers.get('sec-fetch-dest') in [
                'video',
                'audio',
            ]:
                return

            nonlocal last_activity
            pending_requests.add(request)
            last_activity = time.time()

        def on_response(response):
            request = response.request
            if request not in pending_requests:
                return

            # Filter by content type if available
            content_type = response.headers.get('content-type', '').lower()

            # Skip if content type indicates streaming or real-time data
            if any(t in content_type
                   for t in [
                       'streaming',
                       'video',
                       'audio',
                       'webm',
                       'mp4',
                       'event-stream',
                       'websocket',
                       'protobuf']):
                pending_requests.remove(request)
                return

            # Only process relevant content types
            if not any(ct in content_type for ct in RELEVANT_CONTENT_TYPES):
                pending_requests.remove(request)
                return

            # Skip if response is too large (likely not essential for page load)
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 5 * 1024 * 1024:  # 5MB
                pending_requests.remove(request)
                return

            nonlocal last_activity
            pending_requests.remove(request)
            last_activity = time.time()

        # Attach event listeners
        page.on('request', on_request)
        page.on('response', on_response)

        try:
            start_time = time.time()
            while True:
                time.sleep(0.1)
                now = time.time()

                if len(pending_requests) == 0 and (now - last_activity) >= kwargs.get('idle_wait_time', 0.5):
                    break
                if now - start_time > kwargs.get('max_wait_time', 5):
                    logger.debug(
                        f'Network timeout after {kwargs.get("max_wait_time", 5)}s with {len(pending_requests)} '
                        f'pending requests: {[r.url for r in pending_requests]}'
                    )
                    break

        finally:
            # Clean up event listeners
            page.remove_listener('request', on_request)
            page.remove_listener('response', on_response)
        logger.debug(f'Network stabilized for {kwargs.get("idle_wait_time", 0.5)} seconds')

    @staticmethod
    def _enhanced_css_selector_for_element(element: DOMElementNode, include_dynamic_attributes: bool = True) -> str:
        """Creates a CSS selector for a DOM element, handling various edge cases and special characters.

        Args:
                element: The DOM element to create a selector for

        Returns:
                A valid CSS selector string
        """
        try:
            # Get base selector from XPath
            css_selector = DomUtil._convert_simple_xpath_to_css_selector(element.xpath)

            # Handle class attributes
            if 'class' in element.attributes and element.attributes['class'] and include_dynamic_attributes:
                # Define a regex pattern for valid class names in CSS
                valid_class_name_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_-]*$')

                # Iterate through the class attribute values
                classes = element.attributes['class'].split()
                for class_name in classes:
                    # Skip empty class names
                    if not class_name.strip():
                        continue

                    # Check if the class name is valid
                    if valid_class_name_pattern.match(class_name):
                        # Append the valid class name to the CSS selector
                        css_selector += f'.{class_name}'
                    else:
                        # Skip invalid class names
                        continue

            # Expanded set of safe attributes that are stable and useful for selection
            SAFE_ATTRIBUTES = {
                # Data attributes (if they're stable in your application)
                'id',
                # Standard HTML attributes
                'name',
                'type',
                'placeholder',
                # Accessibility attributes
                'aria-label',
                'aria-labelledby',
                'aria-describedby',
                'role',
                # Common form attributes
                'for',
                'autocomplete',
                'required',
                'readonly',
                # Media attributes
                'alt',
                'title',
                'src',
                # Custom stable attributes (add any application-specific ones)
                'href',
                'target',
            }

            if include_dynamic_attributes:
                dynamic_attributes = {
                    'data-id',
                    'data-qa',
                    'data-cy',
                    'data-testid',
                }
                SAFE_ATTRIBUTES.update(dynamic_attributes)

            # Handle other attributes
            for attribute, value in element.attributes.items():
                if attribute == 'class':
                    continue

                # Skip invalid attribute names
                if not attribute.strip():
                    continue

                if attribute not in SAFE_ATTRIBUTES:
                    continue

                # Escape special characters in attribute names
                safe_attribute = attribute.replace(':', r'\:')

                # Handle different value cases
                if value == '':
                    css_selector += f'[{safe_attribute}]'
                elif any(char in value for char in '"\'<>`\n\r\t'):
                    # Use contains for values with special characters
                    # Regex-substitute *any* whitespace with a single space, then strip.
                    collapsed_value = re.sub(r'\s+', ' ', value).strip()
                    # Escape embedded double-quotes.
                    safe_value = collapsed_value.replace('"', '\\"')
                    css_selector += f'[{safe_attribute}*="{safe_value}"]'
                else:
                    css_selector += f'[{safe_attribute}="{value}"]'

            return css_selector

        except Exception:
            # Fallback to a more basic selector if something goes wrong
            tag_name = element.tag_name or '*'
            return f"{tag_name}[highlight_index='{element.highlight_index}']"

    @staticmethod
    def _convert_simple_xpath_to_css_selector(xpath: str) -> str:
        """Converts simple XPath expressions to CSS selectors."""
        if not xpath:
            return ''

        # Remove leading slash if present
        xpath = xpath.lstrip('/')

        # Split into parts
        parts = xpath.split('/')
        css_parts = []

        for part in parts:
            if not part:
                continue

            # Handle index notation [n]
            if '[' in part:
                base_part = part[: part.find('[')]
                index_part = part[part.find('['):]

                # Handle multiple indices
                indices = [i.strip('[]') for i in index_part.split(']')[:-1]]

                for idx in indices:
                    try:
                        # Handle numeric indices
                        if idx.isdigit():
                            index = int(idx) - 1
                            base_part += f':nth-of-type({index + 1})'
                        # Handle last() function
                        elif idx == 'last()':
                            base_part += ':last-of-type'
                        # Handle position() functions
                        elif 'position()' in idx:
                            if '>1' in idx:
                                base_part += ':nth-of-type(n+2)'
                    except ValueError:
                        continue

                css_parts.append(base_part)
            else:
                css_parts.append(part)

        base_selector = ' > '.join(css_parts)
        return base_selector
