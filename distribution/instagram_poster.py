import requests 
import time 
import config 
 
IG_TOKEN      = config.INSTAGRAM_TOKEN 
IG_ACCOUNT_ID = config.INSTAGRAM_BUSINESS_ID 
GRAPH_URL     = "https://graph.facebook.com/v19.0" 
 
def post_image(image_url, caption): 
    try: 
        # Step 1 — Create media container 
        container_url = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media" 
        container_res = requests.post(container_url, data={ 
            "image_url":    image_url, 
            "caption":      caption, 
            "access_token": IG_TOKEN 
        }, timeout=30) 
        container_data = container_res.json() 
        if "id" not in container_data: 
            return {"success": False, "error": container_data} 
        container_id = container_data["id"] 
 
        # Step 2 — Wait for processing 
        time.sleep(5) 
 
        # Step 3 — Publish 
        publish_url = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media_publish" 
        publish_res = requests.post(publish_url, data={ 
            "creation_id":  container_id, 
            "access_token": IG_TOKEN 
        }, timeout=30) 
        publish_data = publish_res.json() 
 
        if "id" in publish_data: 
            return { 
                "success": True, 
                "post_id": publish_data["id"], 
                "url":     f"https://www.instagram.com/p/{publish_data['id']}" 
            } 
        return {"success": False, "error": publish_data} 
 
    except Exception as e: 
        return {"success": False, "error": str(e)} 
 
def post_reel(video_url, caption, thumbnail_url=None): 
    try: 
        container_url = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media" 
        data = { 
            "media_type":   "REELS", 
            "video_url":    video_url, 
            "caption":      caption, 
            "access_token": IG_TOKEN 
        } 
        if thumbnail_url: 
            data["thumb_offset"] = "0" 
        container_res  = requests.post(container_url, data=data, timeout=30) 
        container_data = container_res.json() 
        if "id" not in container_data: 
            return {"success": False, "error": container_data} 
        container_id = container_data["id"] 
 
        # Wait for video processing 
        time.sleep(30) 
 
        publish_url  = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media_publish" 
        publish_res  = requests.post(publish_url, data={ 
            "creation_id":  container_id, 
            "access_token": IG_TOKEN 
        }, timeout=30) 
        publish_data = publish_res.json() 
 
        if "id" in publish_data: 
            return {"success": True, "post_id": publish_data["id"]} 
        return {"success": False, "error": publish_data} 
 
    except Exception as e: 
        return {"success": False, "error": str(e)} 
 
def post_story(image_url): 
    try: 
        container_url = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media" 
        container_res = requests.post(container_url, data={ 
            "image_url":    image_url, 
            "media_type":   "STORIES", 
            "access_token": IG_TOKEN 
        }, timeout=30) 
        container_data = container_res.json() 
        if "id" not in container_data: 
            return {"success": False, "error": container_data} 
        container_id = container_data["id"] 
        time.sleep(5) 
        publish_url  = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media_publish" 
        publish_res  = requests.post(publish_url, data={ 
            "creation_id":  container_id, 
            "access_token": IG_TOKEN 
        }, timeout=30) 
        publish_data = publish_res.json() 
        if "id" in publish_data: 
            return {"success": True, "post_id": publish_data["id"]} 
        return {"success": False, "error": publish_data} 
    except Exception as e: 
        return {"success": False, "error": str(e)} 
 
def get_post_stats(post_id): 
    try: 
        url = (f"{GRAPH_URL}/{post_id}/insights" 
               f"?metric=reach,likes_count,comments_count,saved" 
               f"&access_token={IG_TOKEN}") 
        res  = requests.get(url, timeout=10) 
        data = res.json() 
        stats = {} 
        for item in data.get("data", []): 
            stats[item["name"]] = item["values"][0]["value"] 
        return {"success": True, "stats": stats} 
    except Exception as e: 
        return {"success": False, "error": str(e)} 
 
def verify_token(): 
    try: 
        url = f"{GRAPH_URL}/me?access_token={IG_TOKEN}" 
        res = requests.get(url, timeout=10) 
        return res.status_code == 200 
    except: 
        return False 
