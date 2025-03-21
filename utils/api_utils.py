import requests
import logging
import time
import json
from typing import Dict, Any, Optional
import random

def make_api_request(url: str, method: str = "get", params: Optional[Dict] = None, 
                   data: Optional[Dict] = None, headers: Optional[Dict] = None, 
                   timeout: int = 10, max_retries: int = 3, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:

    if logger is None:
        logger = logging.getLogger()
    
    if headers is None:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    method = method.lower()
    retries = 0
    
    while retries <= max_retries:
        try:
            logger.debug(f"Making {method} request to {url}")
            
            if method == "get":
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
            elif method == "post":
                response = requests.post(url, params=params, json=data, headers=headers, timeout=timeout)
            elif method == "put":
                response = requests.put(url, params=params, json=data, headers=headers, timeout=timeout)
            elif method == "delete":
                response = requests.delete(url, params=params, headers=headers, timeout=timeout)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            if response.status_code in (200, 201, 204):    
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"text": response.text}
                    
            elif response.status_code == 429:
                retries += 1
                if retries <= max_retries:
                    backoff = (2 ** retries) + random.uniform(0, 1)
                    logger.warning(f"Rate limited. Retrying in {backoff:.1f} seconds. Attempt {retries}/{max_retries}")
                    time.sleep(backoff)
                    continue
                else:
                    return {"error": "Rate limited and max retries exceeded", "status_code": response.status_code}
            
            else:
                error_msg = f"API request failed with status code {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text[:100]}"
                
                logger.error(error_msg)
                return {"error": error_msg, "status_code": response.status_code}
                
        except requests.exceptions.Timeout:
            retries += 1
            if retries <= max_retries:
                logger.warning(f"Request timeout. Retrying in {retries} seconds. Attempt {retries}/{max_retries}")
                time.sleep(retries)  
                continue
            else:
                error_msg = f"Request to {url} timed out after {max_retries} retries"
                logger.error(error_msg)
                return {"error": error_msg}
                
        except requests.exceptions.ConnectionError:
            retries += 1
            if retries <= max_retries:
                logger.warning(f"Connection error. Retrying in {retries*2} seconds. Attempt {retries}/{max_retries}")
                time.sleep(retries * 2)  
                continue
            else:
                error_msg = f"Connection to {url} failed after {max_retries} retries"
                logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Unexpected error making request to {url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}
            
    return {"error": "Maximum retries exceeded with no successful response"}

def batch_api_requests(urls: list, method: str = "get", params_list: Optional[list] = None,
                     headers: Optional[Dict] = None, max_concurrent: int = 3,
                     logger: Optional[logging.Logger] = None) -> list:
    if logger is None:
        logger = logging.getLogger()
    
    if params_list is None:
        params_list = [None] * len(urls)
    
    if len(urls) != len(params_list):
        error_msg = "URLs and params_list must have the same length"
        logger.error(error_msg)
        return [{"error": error_msg}] * len(urls)
    
    results = []
    for i in range(0, len(urls), max_concurrent):
        batch_urls = urls[i:i+max_concurrent]
        batch_params = params_list[i:i+max_concurrent]
        batch_results = []
        for j, (url, params) in enumerate(zip(batch_urls, batch_params)):
            result = make_api_request(url, method=method, params=params, headers=headers, logger=logger)
            batch_results.append(result)
            if j < len(batch_urls) - 1:
                time.sleep(0.2)
        
        results.extend(batch_results)
        
        if i + max_concurrent < len(urls):
            logger.debug(f"Completed batch {i//max_concurrent + 1}. Waiting before next batch...")
            time.sleep(1)
    
    return results