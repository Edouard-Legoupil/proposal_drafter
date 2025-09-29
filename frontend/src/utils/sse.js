export const setupSse = (url, onMessage, onError, onTimeout) => {
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing SSE message:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource failed:', error);
      onError(error);
      eventSource.close();
    };

    const timeoutId = setTimeout(() => {
      if (eventSource.readyState !== EventSource.CLOSED) {
        console.warn('SSE connection timed out.');
        onTimeout();
        eventSource.close();
      }
    }, 300000); // 5-minute timeout

    // Return a function to close the connection and clear the timeout
    return () => {
      clearTimeout(timeoutId);
      if (eventSource.readyState !== EventSource.CLOSED) {
        eventSource.close();
      }
    };
  };