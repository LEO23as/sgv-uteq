<script>
  import { navigating } from '$app/stores';

  let progress = $state(0);
  let visible = $state(false);
  let interval = null;

  $effect(() => {
    if ($navigating) {
      visible = true;
      progress = 15;
      clearInterval(interval);
      interval = setInterval(() => {
        if (progress < 85) {
          progress += Math.floor(Math.random() * 12) + 4;
        }
      }, 150);
    } else {
      if (visible) {
        progress = 100;
        clearInterval(interval);
        setTimeout(() => {
          visible = false;
          progress = 0;
        }, 250);
      }
    }
  });
</script>

{#if visible}
  <div class="top-loader-container">
    <div
      class="top-loader-bar"
      style="width: {progress}%;"
    ></div>
  </div>
{/if}

<style>
  .top-loader-container {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    z-index: 10001;
    pointer-events: none;
    background: transparent;
  }

  .top-loader-bar {
    height: 100%;
    background: linear-gradient(90deg, #1b7505, #48bb78, #38a169);
    box-shadow: 0 0 10px rgba(27, 117, 5, 0.7);
    transition: width 0.18s ease-out;
  }
</style>
