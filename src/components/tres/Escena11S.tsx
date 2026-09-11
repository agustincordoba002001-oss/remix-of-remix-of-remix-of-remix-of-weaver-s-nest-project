import { Instance, Instances } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef, type RefObject } from "react";
import * as THREE from "three";

import { ALTO_TORRE, TORRE_A, TORRE_B, generarCiudad } from "./ciudad";
import { CAPITULOS, DURACION, capituloEn } from "./capitulos";

const suave = (x: number) => x * x * (3 - 2 * Math.min(1, Math.max(0, x)));

function Ciudad({ luz }: { luz: number }) {
  const edificios = useMemo(() => generarCiudad(), []);
  return (
    <Instances limit={edificios.length} castShadow receiveShadow>
      <boxGeometry />
      <meshStandardMaterial roughness={0.85} metalness={0.08} />
      {edificios.map((e, i) => (
        <Instance
          key={i}
          position={[e.x, e.alto / 2, e.z]}
          scale={[e.ancho, e.alto, e.fondo]}
          color={new THREE.Color().setHSL(0.09, 0.18, 0.16 + e.tono * 0.16 * (0.55 + luz * 0.65))}
        />
      ))}
    </Instances>
  );
}

function Torre({ x, z, brillo }: { x: number; z: number; brillo: number }) {
  return (
    <group position={[x, 0, z]}>
      <mesh position={[0, ALTO_TORRE / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[1.7, ALTO_TORRE, 1.7]} />
        <meshStandardMaterial
          color={new THREE.Color().setHSL(0.09, 0.12, 0.34 + brillo * 0.22)}
          roughness={0.42}
          metalness={0.35}
        />
      </mesh>
      <mesh position={[0, ALTO_TORRE + 0.12, 0]}>
        <boxGeometry args={[1.75, 0.24, 1.75]} />
        <meshStandardMaterial color="#e8d7b6" roughness={0.6} />
      </mesh>
    </group>
  );
}

function Avion({
  desde,
  hasta,
  t0,
  t1,
  t,
  desvio = 0,
}: {
  desde: [number, number, number];
  hasta: [number, number, number];
  t0: number;
  t1: number;
  t: RefObject<number>;
  desvio?: number;
}) {
  const grupo = useRef<THREE.Group>(null);
  const estela = useRef<THREE.Mesh>(null);
  useFrame(() => {
    const g = grupo.current;
    if (!g) return;
    const p = (t.current - t0) / (t1 - t0);
    const visible = p > 0 && p < 1.08;
    g.visible = visible;
    if (!visible) return;
    const k = Math.min(1, p);
    const x = desde[0] + (hasta[0] - desde[0]) * k + desvio * suave(Math.max(0, (k - 0.55) / 0.45)) * 16;
    const y = desde[1] + (hasta[1] - desde[1]) * k + Math.sin(k * Math.PI) * 3;
    const z = desde[2] + (hasta[2] - desde[2]) * k;
    g.position.set(x, y, z);
    g.lookAt(hasta[0] + desvio * 16, hasta[1], hasta[2]);
    if (estela.current) {
      const largo = 6 + k * 26;
      estela.current.scale.set(1, 1, largo);
      estela.current.position.set(0, 0, -largo / 2 - 0.6);
      const m = estela.current.material as THREE.MeshBasicMaterial;
      m.opacity = 0.28 * (1 - Math.max(0, k - 0.85) / 0.15);
    }
  });
  return (
    <group ref={grupo}>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.16, 0.16, 1.9, 10]} />
        <meshStandardMaterial color="#f2ece1" roughness={0.5} metalness={0.3} />
      </mesh>
      <mesh position={[0, 0, 0.1]}>
        <boxGeometry args={[2.4, 0.08, 0.55]} />
        <meshStandardMaterial color="#dfd6c6" roughness={0.6} />
      </mesh>
      <mesh position={[0, 0.28, -0.75]}>
        <boxGeometry args={[0.08, 0.55, 0.5]} />
        <meshStandardMaterial color="#dfd6c6" roughness={0.6} />
      </mesh>
      <mesh ref={estela}>
        <cylinderGeometry args={[0.07, 0.22, 1, 8]} />
        <meshBasicMaterial color="#ffffff" transparent opacity={0.25} depthWrite={false} />
      </mesh>
    </group>
  );
}

function Haz({ x, tiempo }: { x: number; tiempo: RefObject<number> }) {
  const malla = useRef<THREE.Mesh>(null);
  useFrame(() => {
    const m = malla.current;
    if (!m) return;
    const fuerza = suave(Math.max(0, (tiempo.current - 26.4) / 3.6));
    m.visible = fuerza > 0.01;
    m.scale.set(1, Math.max(0.001, fuerza), 1);
    m.position.set(x, 60 * fuerza, 0);
    (m.material as THREE.MeshBasicMaterial).opacity = 0.2 * fuerza;
  });
  return (
    <mesh ref={malla} visible={false}>
      <cylinderGeometry args={[0.9, 1.3, 120, 20, 1, true]} />
      <meshBasicMaterial
        color="#cfe4ff"
        transparent
        opacity={0}
        side={THREE.DoubleSide}
        depthWrite={false}
      />
    </mesh>
  );
}

export function Escena11S({ onCapitulo }: { onCapitulo: (i: number) => void }) {
  const camObjetivo = useRef(new THREE.Vector3(0, 10, 0));
  const sol = useRef<THREE.DirectionalLight>(null);
  const reloj = useRef(0);
  const ultimo = useRef(-1);
  const t = useRef(0);

  useFrame((state, delta) => {
    reloj.current = (reloj.current + Math.min(delta, 0.05)) % DURACION;
    const tiempo = reloj.current;
    t.current = tiempo;

    const i = capituloEn(tiempo);
    if (i !== ultimo.current) {
      ultimo.current = i;
      onCapitulo(i);
    }
    const actual = CAPITULOS[i];
    const siguiente = CAPITULOS[i + 1];
    if (!actual) return;
    const fin = siguiente ? siguiente.t : DURACION;
    const p = suave((tiempo - actual.t) / (fin - actual.t));

    const desdeCam = new THREE.Vector3(...actual.camara);
    const hastaCam = new THREE.Vector3(...(siguiente ? siguiente.camara : actual.camara));
    const pos = desdeCam.clone().lerp(hastaCam, p);
    const orbita = tiempo * 0.06;
    pos.x += Math.sin(orbita) * 1.6;
    pos.y += Math.cos(orbita * 1.3) * 0.6;
    state.camera.position.lerp(pos, 1 - Math.exp(-3.4 * Math.min(delta, 0.05)));

    const mira = new THREE.Vector3(...actual.mira).lerp(
      new THREE.Vector3(...(siguiente ? siguiente.mira : actual.mira)),
      p,
    );
    camObjetivo.current.lerp(mira, 1 - Math.exp(-3.4 * Math.min(delta, 0.05)));
    state.camera.lookAt(camObjetivo.current);

    if (sol.current) {
      const alba = Math.min(1, tiempo / 10);
      sol.current.position.set(-34 + alba * 16, 4 + alba * 22, -26);
      sol.current.intensity = 1.1 + alba * 1.5;
      sol.current.color.setHSL(0.075 + alba * 0.02, 0.62 - alba * 0.32, 0.6 + alba * 0.14);
    }
  });

  return (
    <>
      <color attach="background" args={["#0d1626"]} />
      <fog attach="fog" args={["#20304a", 44, 118]} />
      <hemisphereLight args={["#8fb4e6", "#2b2118", 0.55]} />
      <ambientLight intensity={0.24} />
      <directionalLight
        ref={sol}
        castShadow
        intensity={1.5}
        color="#ffb867"
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        shadow-camera-left={-50}
        shadow-camera-right={50}
        shadow-camera-top={50}
        shadow-camera-bottom={-50}
        shadow-camera-far={160}
      />

      <mesh rotation-x={-Math.PI / 2} receiveShadow>
        <planeGeometry args={[300, 300]} />
        <meshStandardMaterial color="#141d2c" roughness={0.95} />
      </mesh>
      <mesh rotation-x={-Math.PI / 2} position={[0, 0.02, 46]}>
        <planeGeometry args={[300, 120]} />
        <meshStandardMaterial color="#16283f" roughness={0.22} metalness={0.55} />
      </mesh>

      <Ciudad luz={0.8} />
      <Torre x={TORRE_A[0]} z={TORRE_A[1]} brillo={0.8} />
      <Torre x={TORRE_B[0]} z={TORRE_B[1]} brillo={0.8} />

      <Avion desde={[-58, 22, -34]} hasta={[46, 26, -18]} t0={11.6} t1={19} t={t} />
      <Avion desde={[-62, 18, 26]} hasta={[42, 24, 34]} t0={12.6} t1={20} t={t} />
      <Avion desde={[54, 24, -40]} hasta={[-46, 22, -8]} t0={13.4} t1={21} t={t} />
      <Avion desde={[-70, 26, -8]} hasta={[30, 24, -4]} t0={13} t1={22} t={t} desvio={-1} />

      <Haz x={TORRE_A[0]} tiempo={t} />
      <Haz x={TORRE_B[0]} tiempo={t} />
    </>
  );
}
