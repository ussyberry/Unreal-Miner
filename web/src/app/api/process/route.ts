import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { s1Path, s2Path, demPath, outputDir, demoMode = true } = body;

        // Validate required parameters
        if (!s1Path || !s2Path || !demPath || !outputDir) {
            return NextResponse.json(
                { error: 'Missing required parameters: s1Path, s2Path, demPath, outputDir' },
                { status: 400 }
            );
        }

        const projectRoot = path.resolve(process.cwd(), '..');
        
        // Construct command to run the processing pipeline
        const cmd = `cd "${projectRoot}" && python -m unreal_miner.process_fusion \
            --s1-path "${s1Path}" \
            --s2-path "${s2Path}" \
            --dem-path "${demPath}" \
            --output-dir "${outputDir}" \
            ${demoMode ? '--demo-mode' : ''} \
            --tile-id "web_job_${Date.now()}"`;

        console.log('Executing processing job:', cmd);

        // Execute the processing command
        const { stdout, stderr } = await execAsync(cmd, {
            timeout: 300000, // 5 minute timeout
            maxBuffer: 1024 * 1024 * 10 // 10MB buffer
        });

        if (stderr && !stderr.includes('WARNING')) {
            console.error('Processing stderr:', stderr);
            return NextResponse.json(
                { error: 'Processing failed', details: stderr },
                { status: 500 }
            );
        }

        // Return success response with job details
        return NextResponse.json({
            success: true,
            message: 'Processing completed successfully',
            jobId: `web_job_${Date.now()}`,
            output: {
                stdout: stdout.trim(),
                outputDir: outputDir,
                files: [
                    'classification_map.tif',
                    'feature_stack.tif',
                    'meta.json'
                ]
            }
        });

    } catch (error: any) {
        console.error('Processing failed:', error);
        
        // Handle timeout specifically
        if (error.code === 'ETIMEDOUT') {
            return NextResponse.json(
                { error: 'Processing timeout - job took too long to complete' },
                { status: 408 }
            );
        }

        return NextResponse.json(
            { 
                error: 'Failed to process satellite data',
                details: error.message || 'Unknown error occurred'
            },
            { status: 500 }
        );
    }
}