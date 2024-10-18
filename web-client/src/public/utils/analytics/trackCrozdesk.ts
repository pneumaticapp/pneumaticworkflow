export function trackCrozdesk() {
  const scriptNode = document.createElement('script');
  scriptNode.type = 'text/javascript';
  scriptNode.async = true;
  scriptNode.src = 'https://trk.crozdesk.com/59VrWJZLLNZYNB_z4J6U';
  
  const firstScriptNode = document.getElementsByTagName('script')[0];
  firstScriptNode.parentNode?.insertBefore(scriptNode, firstScriptNode);
}
