'use strict';
(() => {
  const demo = document.querySelector('[data-traffic-demo]');
  if (!demo) return;
  const ru = document.documentElement.lang === 'ru';
  const run = demo.querySelector('[data-run]');
  const label = demo.querySelector('[data-label]');
  const strip = demo.querySelector('[data-states]');
  let state = 0, timer = null;
  const names = ru ? ['красный', 'жёлтый', 'зелёный'] : ['red', 'yellow', 'green'];
  for (let i=0;i<10;i++) { const x=document.createElement('span'); x.textContent='S'+i; strip.append(x); }
  function render() {
    const color = state<4 ? 0 : state<6 ? 1 : 2;
    demo.querySelectorAll('.lamp').forEach((el,i) => { el.classList.toggle('on',i===color); el.querySelector('.level').textContent=i===color?'1':'0'; });
    [...strip.children].forEach((el,i)=>el.classList.toggle('active',i===state));
    label.textContent=(ru?'Состояние ':'State ')+'S'+state+' · '+names[color]+' · '+(ru?'следующее ':'next ')+'S'+((state+1)%10);
    run.textContent=timer ? (ru?'Пауза':'Pause') : (ru?'Пуск · 1 Гц':'Run · 1 Hz');
    run.setAttribute('aria-pressed',timer?'true':'false');
  }
  function pause(){if(timer)clearInterval(timer);timer=null;}
  function step(){state=(state+1)%10;render();}
  run.addEventListener('click',()=>{if(timer)pause();else timer=setInterval(step,1000);render();});
  demo.querySelector('[data-step]').addEventListener('click',()=>{pause();step();});
  demo.querySelector('[data-reset]').addEventListener('click',()=>{pause();state=0;render();});
  render();
})();
