## Frontend API Connection Issues

If you see these errors:
```
failed to get pages: undefined
MaxListenersExceededWarning: Possible EventEmitter memory leak detected
```

### Solution:
1. **Restart nginx to apply new configuration**:
   ```bash
   docker compose restart nginx
   ```

2. **Restart frontend and backend**:
   ```bash
   docker compose restart pneumatic-frontend pneumatic-backend
   ```

3. **Check backend logs**:
   ```bash
   docker compose logs pneumatic-backend
   ```

4. **Check frontend logs**:
   ```bash
   docker compose logs pneumatic-frontend
   ```

5. **Verify API endpoints**:
   ```bash
   curl http://localhost/api/
   curl http://localhost/admin/
   ```

6. **Check nginx logs**:
   ```bash
   docker compose logs nginx
   ```
