            except urllib.error.HTTPError as err:
                raw = err.read().decode("utf-8", errors="replace")
                try:
                    detail = json.loads(raw)["error"]["message"]
                except (ValueError, KeyError, TypeError):
                    detail = raw or str(err)

                detail = str(detail).replace(api_key.strip(), "[REDACTED]")
                st.error(f"Groq API त्रुटि ({err.code}): {detail[:1500]}")
